import { linkSource, uploadAsset } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { Badge, Empty, Select } from "@/components/fields";
import type { Dictionary } from "@/lib/i18n";
import type { Project, Work } from "@/lib/types";

type Props = { works: Work[]; dict: Dictionary; projects?: Project[]; allowUpload?: boolean };

export function SourceList({ works, dict, projects = [], allowUpload = true }: Props) {
  const ui = dict.ui;
  if (!works.length) return <Empty>{ui.noSources}</Empty>;
  return (
    <ul className="space-y-3" data-testid="source-list">
      {works.map((work) => (
        <li key={work.id} className="space-y-2 rounded-md border border-[var(--color-border)] p-3 text-sm" data-testid="source-work">
          <div className="flex flex-wrap items-center gap-2">
            <span dir="auto" className="font-medium">
              {work.title}
            </span>
            {work.authors.length ? <span className="text-[var(--color-muted)]">— {work.authors.join("; ")}</span> : null}
            <Badge>{work.authority_layer}</Badge>
          </div>
          {work.editions.map((edition) => (
            <div key={edition.id} className="space-y-2 border-s-2 border-[var(--color-border)] ps-3">
              <div className="flex flex-wrap items-center gap-2">
                <span>
                  {ui.edition}: {edition.edition_label ?? "—"}
                  {edition.language ? ` (${edition.language})` : ""}
                </span>
                <span data-testid="verification-state">
                  <Badge>{edition.verification_state}</Badge>
                </span>
                <span data-testid="availability">
                  <Badge tone={edition.available ? "good" : "warn"}>{edition.available ? ui.available : ui.unavailable}</Badge>
                </span>
              </div>
              {edition.assets.length ? (
                <ul className="space-y-1">
                  {edition.assets.map((asset) => (
                    <li key={asset.id} className="flex flex-wrap items-center gap-2">
                      <Badge>{asset.kind}</Badge>
                      <Badge>{asset.access_mode}</Badge>
                      {asset.original_filename ?? asset.holding_note ?? ""}
                      {asset.ingestion_status !== "NOT_APPLICABLE" ? (
                        <span data-testid="ingestion-status">
                          <Badge tone={asset.ingestion_status === "COMPLETE" ? "good" : asset.ingestion_status === "FAILED" ? "warn" : "neutral"}>
                            {ui.ingestion}: {asset.ingestion_status}
                          </Badge>
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : null}
              {allowUpload ? (
                <ActionForm action={uploadAsset} submitLabel={ui.upload} pendingLabel={ui.uploading} successMessage={ui.uploaded} className="flex flex-wrap items-center gap-2">
                  <input type="hidden" name="edition_id" value={edition.id} />
                  <input type="file" name="file" required accept=".pdf,.txt,.epub,.png,.jpg,.jpeg,application/pdf,text/plain" aria-label={ui.chooseFile} className="text-sm" />
                </ActionForm>
              ) : null}
            </div>
          ))}
          {projects.length ? (
            <ActionForm action={linkSource} submitLabel={ui.addToProject} pendingLabel={ui.linking} className="flex flex-wrap items-center gap-2">
              <input type="hidden" name="work_id" value={work.id} />
              <Select name="project_id" aria-label={ui.linkToProject}>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </Select>
            </ActionForm>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
