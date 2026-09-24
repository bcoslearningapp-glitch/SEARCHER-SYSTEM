import { Badge } from "@/components/fields";
import type { OutputStrings } from "@/lib/i18n-outputs";
import type { Output, OutputBlock } from "@/lib/types";

/** Preview of an output version in its mode (FR-OUT-001). Quotes render verbatim and are marked protected. */
export function OutputBlocks({ output, blocks, t }: { output: Output; blocks: OutputBlock[]; t: OutputStrings }) {
  const referenced = output.mode !== "READABLE";
  const audit = output.mode === "AUDIT";
  const dir = output.language === "ar" ? "rtl" : "ltr";
  const quoteNumbers = blocks.reduce<number[]>((acc, b) => [...acc, (acc.at(-1) ?? 0) + (b.kind === "QUOTE" ? 1 : 0)], []);
  return (
    <article dir={dir} lang={output.language} className="space-y-3" data-testid="output-preview">
      {blocks.map((block, i) => {
        const meta = (
          <>
            {referenced && block.label ? <Badge>{block.label}</Badge> : null}
            {audit && block.trace.length ? (
              <span className="block text-xs text-[var(--color-muted)]" dir="ltr">
                {t.trace}: {block.trace.map((tr) => `${tr.entity_type}:${tr.entity_id.slice(0, 8)}`).join(", ")}
              </span>
            ) : null}
          </>
        );
        switch (block.kind) {
          case "HEADING": {
            const Tag = block.level && block.level > 2 ? "h4" : "h3";
            return (
              <Tag key={i} className="font-semibold">
                {block.text}
              </Tag>
            );
          }
          case "QUOTE": {
            const quoteNumber = quoteNumbers[i];
            return (
              <blockquote key={i} className="border-s-4 border-[var(--color-accent)] ps-3" data-testid="protected-quote">
                <p dir="auto" className={block.quote?.source_kind === "QURAN" ? "quran-text" : undefined}>
                  {block.quote?.text ?? block.text}
                  {referenced ? <sup className="ms-1">[{quoteNumber}]</sup> : null}
                </p>
                {referenced ? (
                  <span className="text-xs text-[var(--color-muted)]">
                    {t.protectedQuote}
                    {block.quote?.quran_ref ? ` · ${block.quote.quran_ref}` : ""}
                  </span>
                ) : null}
                {meta}
              </blockquote>
            );
          }
          case "LIST":
            return (
              <div key={i}>
                {referenced && block.label ? <Badge>{block.label}</Badge> : null}
                <ul className="list-disc ps-5">
                  {(block.items ?? []).map((item, j) => (
                    <li key={j} dir="auto">
                      {item}
                    </li>
                  ))}
                </ul>
                {audit ? meta : null}
              </div>
            );
          default:
            return (
              <p key={i} dir="auto" className={block.kind === "CLAIM" ? "font-medium" : block.kind === "NOTE" ? "text-sm text-[var(--color-muted)]" : undefined}>
                {block.text} {meta}
              </p>
            );
        }
      })}
    </article>
  );
}
