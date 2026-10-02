import { describe, expect, it } from "vitest";
import { adoption, lineDiff } from "./api";

describe("audit calculations", () => {
  it("uses latest feedback and separates evaluations", () => {
    const records = ["accept", "reject"].map((action, i) => ({
      id: String(i),
      kind: "feedback",
      versionId: "v1",
      createdAt: "",
      payload: { evaluationId: "e1", suggestionId: "s1", action },
    }));
    expect(adoption(records, "v1")).toMatchObject({
      reviewed: 1,
      accepted: 0,
      rate: 0,
    });
    expect(adoption(records, "v2").rate).toBeNull();
  });
  it("diff handles repeated lines and replacement", () => {
    expect(lineDiff("A\nA\nB", "A\nC\nB")).toEqual({
      removed: ["A"],
      added: ["C"],
    });
  });
});
