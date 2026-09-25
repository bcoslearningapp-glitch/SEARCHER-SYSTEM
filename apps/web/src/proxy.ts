import { NextResponse, type NextRequest } from "next/server";

/**
 * Host allow-list (#55, PRD §68). The app serves research data to whoever can reach it on the local port.
 * Refusing unknown Host names defeats DNS rebinding, where an attacker's domain resolves to 127.0.0.1 and the
 * browser treats this app as same-origin with the attacker's page.
 */
const ALLOWED = new Set(
  (process.env.WEB_ALLOWED_HOSTS ?? "localhost,127.0.0.1,[::1]")
    .split(",")
    .map((h) => h.trim().toLowerCase())
    .filter(Boolean),
);

export function hostName(host: string): string {
  const value = host.toLowerCase();
  if (value.startsWith("[")) return value.slice(0, value.indexOf("]") + 1);
  return value.split(":")[0] ?? "";
}

export function proxy(request: NextRequest) {
  if (ALLOWED.has("*") || ALLOWED.has(hostName(request.headers.get("host") ?? ""))) return NextResponse.next();
  return new NextResponse("This host name is not served by the research app.", { status: 403 });
}
