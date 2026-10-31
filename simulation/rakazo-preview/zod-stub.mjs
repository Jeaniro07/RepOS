// Minimal subset of zod used by Rakazo's plugin manifest schema (object/string/array/optional/strict/min/max/regex).
class S {
  constructor(check, extra = {}) { this.check = check; Object.assign(this, extra); this.isOptional = false; }
  optional() { const s = new S(this.check, { shape: this.shape }); s.isOptional = true; return s; }
  safeParse(v) { const e = this.run(v); return e ? { success: false, error: e } : { success: true, data: v }; }
  run(v) { if (v === undefined) return this.isOptional ? null : "required"; return this.check(v); }
}
const string = () => {
  const rules = [];
  const s = new S((v) => (typeof v !== "string" ? "not a string" : rules.map((r) => r(v)).find(Boolean) || null));
  s.min = (n) => { rules.push((v) => (v.length < n ? `min ${n}` : null)); return s; };
  s.max = (n) => { rules.push((v) => (v.length > n ? `max ${n}` : null)); return s; };
  s.regex = (re) => { rules.push((v) => (re.test(v) ? null : `regex ${re}`)); return s; };
  return s;
};
const array = (item) => new S((v) => (!Array.isArray(v) ? "not an array" : v.map((x) => item.run(x)).find(Boolean) || null));
const object = (shape) => {
  let strict = false;
  const s = new S((v) => {
    if (typeof v !== "object" || v === null || Array.isArray(v)) return "not an object";
    for (const [k, sch] of Object.entries(shape)) { const e = sch.run(v[k]); if (e) return `${k}: ${e}`; }
    if (strict) { const extra = Object.keys(v).filter((k) => !(k in shape)); if (extra.length) return `unknown keys ${extra}`; }
    return null;
  }, { shape });
  s.strict = () => { strict = true; return s; };
  return s;
};
export const z = { object, string, array };
export default z;
