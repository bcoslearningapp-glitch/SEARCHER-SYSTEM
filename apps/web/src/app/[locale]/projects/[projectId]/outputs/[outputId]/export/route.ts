import { apiRaw } from "@/lib/api";

const UUID = /^[0-9a-f-]{36}$/i;
const FORMATS = new Set(["md", "html", "docx", "pdf"]);

/** Download an output version as Markdown, HTML, DOCX or PDF (FR-OUT-006), proxied from the API. */
export async function GET(request: Request, { params }: { params: Promise<{ projectId: string; outputId: string }> }) {
  const { projectId, outputId } = await params;
  const url = new URL(request.url);
  const version = url.searchParams.get("version") ?? "";
  const requested = url.searchParams.get("format") ?? "md";
  const format = FORMATS.has(requested) ? requested : "md";
  if (![projectId, outputId, version].every((id) => UUID.test(id))) return new Response("Not found", { status: 404 });
  const upstream = await apiRaw(`/api/v1/projects/${projectId}/outputs/${outputId}/versions/${version}/export?format=${format}`);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/octet-stream",
      "Content-Disposition": upstream.headers.get("content-disposition") ?? "attachment",
    },
  });
}
