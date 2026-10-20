import { expect, test } from "bun:test";
import { toSkill } from "../teach/draft-to-skill.ts";

const draft = await Bun.file(`${import.meta.dir}/fixtures/draft.json`).json();

test("draft -> SKILL.md memakai tool MCP milik server", () => {
  const { markdown: md } = toSkill(draft, "ops");
  expect(md.startsWith("---\n")).toBe(true);
  expect(md).toContain("mcp__ops__browser_");
  expect(md).not.toMatch(/computer_(click|type|navigate)/);
  expect(md).toContain("tidak memberi izin");
});

test("slug berbahaya ditolak", () => {
  expect(() => toSkill({ ...draft, slug: "../../etc" }, "ops")).toThrow();
  expect(() => toSkill({ ...draft, slug: "Besar Spasi" }, "ops")).toThrow();
});
