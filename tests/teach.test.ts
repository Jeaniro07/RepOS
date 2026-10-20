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

test("tool yang sudah bernama browser_* tidak diberi prefiks dua kali", () => {
  const d = { ...draft, requiredTools: ["computer_type", "browser_type"], instructions: "Pakai computer_type lalu browser_type." };
  const { markdown } = toSkill(d, "ops");
  expect(markdown).not.toContain("mcp__ops__mcp__ops__");
  expect(markdown).toContain("Pakai mcp__ops__browser_type lalu mcp__ops__browser_type.");
});

test("field draft tidak bisa menyisipkan kunci front matter", () => {
  const { markdown } = toSkill({ ...draft, sourceRecordingId: "a\nevil: true" }, "ops");
  expect(markdown).not.toMatch(/^evil:/m);
});
