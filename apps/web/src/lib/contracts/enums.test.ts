import { describe, expect, it } from "vitest";

import { ProjectStatusValues, ReferenceJudgmentStateValues, SourceVerificationStateValues } from "./enums";

describe("generated Research Core enums", () => {
  it("keeps NOT_IN_CONFLICT distinct from REFERENCE_SUPPORTED (Core §8)", () => {
    expect(ReferenceJudgmentStateValues).toContain("NOT_IN_CONFLICT");
    expect(ReferenceJudgmentStateValues).toContain("REFERENCE_SUPPORTED");
  });

  it("exposes the full project lifecycle and verification vocabulary", () => {
    expect(ProjectStatusValues).toHaveLength(8);
    expect(SourceVerificationStateValues).toContain("METADATA_ONLY");
  });
});
