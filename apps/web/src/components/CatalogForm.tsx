import { catalogSource } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { Field, Select, TextInput } from "@/components/fields";
import { ReferenceAuthorityLayerValues } from "@/lib/contracts/enums";
import type { Dictionary } from "@/lib/i18n";

export function CatalogForm({ dict, projectId }: { dict: Dictionary; projectId?: string }) {
  const ui = dict.ui;
  return (
    <ActionForm action={catalogSource} submitLabel={ui.catalog} pendingLabel={ui.cataloging} testId="catalog-form">
      {projectId ? <input type="hidden" name="project_id" value={projectId} /> : null}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label={ui.workTitle}>
          <TextInput name="title" required />
        </Field>
        <Field label={ui.authors}>
          <TextInput name="authors" />
        </Field>
        <Field label={ui.authorityLayer}>
          <Select name="authority_layer" defaultValue="SCIENTIFIC_EXPERIMENTAL">
            {ReferenceAuthorityLayerValues.map((v) => (
              <option key={v}>{v}</option>
            ))}
          </Select>
        </Field>
        <Field label={ui.editionLabel}>
          <TextInput name="edition_label" />
        </Field>
        <Field label={ui.language}>
          <TextInput name="language" placeholder="ar / en / fr" />
        </Field>
        <Field label={ui.publisher}>
          <TextInput name="publisher" />
        </Field>
        <Field label={ui.holding}>
          <Select name="holding" defaultValue="">
            <option value="">{ui.holdingNone}</option>
            <option value="PHYSICAL">{ui.holdingPhysical}</option>
            <option value="RESTRICTED">{ui.holdingRestricted}</option>
          </Select>
        </Field>
        <Field label={ui.holdingNote}>
          <TextInput name="holding_note" />
        </Field>
      </div>
    </ActionForm>
  );
}
