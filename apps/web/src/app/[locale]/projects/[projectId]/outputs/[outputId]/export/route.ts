import { apiRaw } from "@/lib/api";

const UUID = /^[0-9a-f-]{36}$/i;

/** Download an output version as Markdown or HTML (FR-OUT-006), proxied from the API. */
export async function GET(request: Request, { params }: { params: Promise<{ projectId: string; outputId: string }> }) {
  const { projectId, outputId } = await params;
  const url = new URL(request.url);
  const version = url.searchParams.get("version") ?? "";
  const format = url.searchParams.get("format") === "html" ? "html" : "md";
  if (![projectId, outputId, version].every((id) => UUID.test(id))) return new Response("Not found", { status: 404 });
  const upstream = await apiRaw(`/api/v1/projects/${projectId}/outputs/${outputId}/versions/${version}/export?format=${format}`);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "text/plain",
      "Content-Disposition": upstream.headers.get("content-disposition") ?? "attachment",
    },
  });
}
