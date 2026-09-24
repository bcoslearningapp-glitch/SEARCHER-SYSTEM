import { apiRaw } from "@/lib/api";

/** Download the project's Research Core Package (FR-PORT-001), proxied from the API. */
export async function GET(_: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(projectId)) return new Response("Not found", { status: 404 });
  const upstream = await apiRaw(`/api/v1/projects/${projectId}/package`);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/zip",
      "Content-Disposition": upstream.headers.get("content-disposition") ?? "attachment",
    },
  });
}
