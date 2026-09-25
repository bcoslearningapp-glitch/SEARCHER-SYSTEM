"""HTTP boundary protections for a local-first service (PRD §68, #55).

The API has no browser clients: the web app calls it server-side. It still listens on a local port, and any
web page open in the researcher's browser can send requests to it. Three protections apply:
- **Host allow-list.** A request must name a known host. This defeats DNS rebinding, where an attacker's
  domain resolves to 127.0.0.1 and the browser treats the API as same-origin.
- **Cross-site request refusal.** An unsafe method carrying a foreign `Origin`, or `Sec-Fetch-Site: cross-site`,
  is refused. Multipart uploads and body-less POSTs are "simple" requests that skip the CORS preflight, so
  CORS alone does not stop them.
- **Response headers.** No sniffing, no framing, no referrer, and a CSP that allows nothing to load.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; sandbox",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def _refused(code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=403, content={"error": {"code": code, "message": message, "details": {}}})


class BoundaryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, allowed_hosts: list[str], allowed_origins: list[str]) -> None:
        super().__init__(app)
        self.hosts = {h.lower() for h in allowed_hosts}
        self.origins = {o.rstrip("/").lower() for o in allowed_origins}

    def _host_allowed(self, request: Request) -> bool:
        host = request.headers.get("host", "").lower()
        if host.startswith("["):  # IPv6 literal, e.g. [::1]:8000
            name = host[1 : host.find("]")] if "]" in host else host
        else:
            name = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
        return "*" in self.hosts or name in self.hosts

    def _cross_site(self, request: Request) -> bool:
        if request.method in SAFE_METHODS:
            return False
        origin = request.headers.get("origin")
        if origin is not None and origin.rstrip("/").lower() not in self.origins:
            return True
        return request.headers.get("sec-fetch-site") == "cross-site"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not self._host_allowed(request):
            response: Response = _refused("host_not_allowed", "this host name is not served by the research API")
        elif self._cross_site(request):
            response = _refused("cross_site_request", "cross-site requests cannot change research data")
        else:
            response = await call_next(request)
        for name, value in HEADERS.items():
            response.headers.setdefault(name, value)
        return response
