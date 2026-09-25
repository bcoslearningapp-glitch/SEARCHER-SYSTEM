import { describe, expect, it } from "vitest";

import { hostName } from "@/proxy";

describe("hostName", () => {
  it("strips the port and keeps IPv6 brackets", () => {
    expect(hostName("localhost:3000")).toBe("localhost");
    expect(hostName("127.0.0.1")).toBe("127.0.0.1");
    expect(hostName("[::1]:3000")).toBe("[::1]");
    expect(hostName("Attacker.Example:3000")).toBe("attacker.example");
  });
});
