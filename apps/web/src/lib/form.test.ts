import { describe, expect, it } from "vitest";

import { frameFromForm, lines } from "./form";

describe("form helpers", () => {
  it("splits list fields into trimmed non-empty lines", () => {
    expect(lines(" a \n\n b\r\nc ")).toEqual(["a", "b", "c"]);
  });

  it("builds a complete Problem Frame payload", () => {
    const form = new FormData();
    form.set("central_issue", " Disengagement ");
    form.set("unknowns", "Pay\nCommute");
    const content = frameFromForm(form);
    expect(content.central_issue).toBe("Disengagement");
    expect(content.unknowns).toEqual(["Pay", "Commute"]);
    expect(content.constraints).toEqual([]);
    expect(content.gap).toBe("");
  });
});
