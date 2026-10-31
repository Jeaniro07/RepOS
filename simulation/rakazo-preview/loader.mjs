// Resolve Rakazo's workspace imports to its own source files or to the local stubs.
import { pathToFileURL } from "node:url";
import { existsSync } from "node:fs";
const RAKAZO = process.env.RAKAZO_SRC;
const here = new URL("./", import.meta.url);
const map = {
  zod: new URL("zod-stub.mjs", here).href,
  "@rakazo/contracts": new URL("contracts-stub.mjs", here).href,
  "@rakazo/core": pathToFileURL(`${RAKAZO}/packages/core/src/agent-skill.ts`).href,
};
export async function resolve(specifier, context, next) {
  if (map[specifier]) return { url: map[specifier], shortCircuit: true };
  if (specifier === "./connector-http.js") return { url: new URL("connector-http-stub.mjs", here).href, shortCircuit: true };
  if (specifier === "./web-ssrf.js") return { url: new URL("web-ssrf-stub.mjs", here).href, shortCircuit: true };
  if (specifier.startsWith(".") && specifier.endsWith(".js") && context.parentURL?.endsWith(".ts")) {
    const ts = new URL(specifier.replace(/\.js$/, ".ts"), context.parentURL);
    if (existsSync(ts)) return { url: ts.href, shortCircuit: true };
  }
  return next(specifier, context);
}
