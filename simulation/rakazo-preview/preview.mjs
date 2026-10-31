// Run Rakazo's real parsePluginDirectory() on a local plugin folder, as Integrations → From GitHub → Preview does.
// Usage: RAKAZO_SRC=/path/to/rakazo node --experimental-strip-types --import ./register.mjs preview.mjs <plugin-dir>
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { pathToFileURL } from "node:url";
const dir = process.argv[2];
const { parsePluginDirectory } = await import(pathToFileURL(`${process.env.RAKAZO_SRC}/packages/adapters/src/plugin-connectors.ts`).href);
const files = [];
const walk = (d) => { for (const f of readdirSync(d)) { const p = join(d, f); statSync(p).isDirectory() ? walk(p) : files.push({ path: relative(dir, p).split("\\").join("/"), content: readFileSync(p, "utf8") }); } };
walk(dir);
const sha = "0".repeat(40);
const plugin = parsePluginDirectory({ files, resolvedSha: sha });
const summary = {
  name: plugin.name, version: plugin.version, format: plugin.format,
  skills: plugin.skills.map((s) => ({ name: s.name, files: Object.keys(s.files ?? {}).length })),
  mcpServers: plugin.mcpServers, skipped: plugin.skipped, builtinNames: plugin.builtinNames,
};
console.log(JSON.stringify(summary, null, 2));
process.exit(plugin.skipped.length || plugin.builtinNames.length ? 1 : 0);
