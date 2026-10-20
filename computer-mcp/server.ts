// Sidecar MCP: membungkus satu agent-computer OpenBot jadi tool MCP untuk Hermes.
// Satu file, nol dependensi (Bun). MCP "Streamable HTTP" tanpa sesi: POST JSON-RPC -> JSON.
// Lapis kedua pagar Auto Review: domain allowlist di sini + egress policy di Chromium.

const env = (k: string, d = "") => process.env[k]?.trim() || d;
const COMPUTER = env("COMPUTER_URL", "http://localhost:4100");
const TOKEN = env("COMPUTER_TOKEN"); // sidecar -> komputer; hanya sidecar yang memegangnya
const MCP_TOKEN = env("MCP_TOKEN"); // Hermes -> sidecar; tidak berlaku di komputer (yang punya /exec)
const BOT = env("BOT_ID", "bot");
const PORT = Number(env("PORT", "8700"));
const EGRESS_REFRESH_MS = Number(env("EGRESS_REFRESH_MS", "30000"));
const ALLOWED = env("ALLOWED_DOMAINS").split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);

type Json = Record<string, unknown>;
type Content = { type: "text"; text: string } | { type: "image"; data: string; mimeType: string };

export const hostAllowed = (url: string, allowed = ALLOWED): boolean => {
  if (allowed.includes("*")) return true;
  let host: string;
  try {
    const u = new URL(url);
    if (u.protocol !== "https:" && u.protocol !== "http:") return false;
    host = u.hostname.toLowerCase();
  } catch {
    return false;
  }
  return allowed.some((d) => host === d || host.endsWith(`.${d.replace(/^\*\./, "")}`));
};

async function call(path: string, method = "GET", body?: Json): Promise<Json> {
  const res = await fetch(COMPUTER + path, {
    method,
    headers: { "x-openbot-computer-token": TOKEN, "x-openbot-bot-id": BOT, "content-type": "application/json" },
    body: body && JSON.stringify(body),
  });
  const data = (await res.json().catch(() => ({}))) as Json;
  if (!res.ok) throw new Error(String(data.error ?? `${path} -> HTTP ${res.status}`));
  return data;
}

const text = (v: unknown): Content[] => [{ type: "text", text: typeof v === "string" ? v : JSON.stringify(v) }];
const str = (a: Json, k: string) => {
  if (typeof a[k] !== "string" || !a[k]) throw new Error(`argumen '${k}' wajib (string)`);
  return a[k] as string;
};
const act = (a: Json, extra: Json) => ({ ...extra, ...(a.snapshotId !== undefined && { snapshotId: a.snapshotId }) });

type Tool = { description: string; props?: Json; required?: string[]; run: (a: Json) => Promise<Content[]> };
const s = (description: string) => ({ type: "string", description });
const snap = { snapshotId: { type: "number", description: "snapshotId dari browser_snapshot terakhir" } };

export const tools: Record<string, Tool> = {
  browser_navigate: {
    description: "Buka URL di browser bot. Hanya domain yang diizinkan.",
    props: { url: s("URL http(s)") }, required: ["url"],
    run: async (a) => {
      const url = str(a, "url");
      if (!hostAllowed(url)) throw new Error(`domain tidak diizinkan untuk bot ini: ${url}`);
      return text(await call("/navigate", "POST", { url }));
    },
  },
  browser_snapshot: {
    description: "Daftar elemen halaman beserta ref (pakai ref ini untuk click/type).",
    run: async () => text(await call("/snapshot", "POST", {})),
  },
  browser_read: { description: "Teks halaman yang sedang dibuka.", run: async () => text(await call("/read")) },
  browser_screenshot: {
    description: "Tangkapan layar halaman (kolom sensitif sudah ditutup).",
    run: async () => {
      const r = await call("/screenshot");
      return [{ type: "image", data: String(r.base64), mimeType: "image/png" }];
    },
  },
  browser_click: {
    description: "Klik elemen berdasarkan ref.", props: { ref: s("ref elemen"), ...snap }, required: ["ref"],
    run: async (a) => text(await call("/click", "POST", act(a, { ref: str(a, "ref") }))),
  },
  browser_type: {
    description: "Isi teks ke kolom berdasarkan ref.",
    props: { ref: s("ref kolom"), text: s("teks"), submit: { type: "boolean" }, ...snap }, required: ["ref", "text"],
    run: async (a) => text(await call("/type", "POST", act(a, { ref: str(a, "ref"), text: String(a.text ?? ""), submit: a.submit === true }))),
  },
  browser_key: {
    description: "Tekan tombol (Enter, Tab, ...).", props: { key: s("nama tombol"), ref: s("ref opsional"), ...snap }, required: ["key"],
    run: async (a) => text(await call("/key", "POST", act(a, { key: str(a, "key"), ...(a.ref ? { ref: a.ref } : {}) }))),
  },
  browser_scroll: {
    description: "Gulir halaman.", props: { deltaY: { type: "number", description: "piksel; negatif = ke atas" } }, required: ["deltaY"],
    run: async (a) => text(await call("/scroll", "POST", act(a, { deltaY: Number(a.deltaY) }))),
  },
  request_help: {
    description: "Minta manusia mengambil alih browser (login, CAPTCHA, 2FA). Jangan minta kata sandi lewat chat.",
    props: { reason: s("alasan singkat") }, required: ["reason"],
    run: async (a) => text(await call("/control/request", "POST", { reason: str(a, "reason") })),
  },
  files_list: {
    description: "Daftar berkas di workspace bot.", props: { path: s("folder, default akar") },
    run: async (a) => text(await call("/files/list", "POST", { path: a.path ?? "" })),
  },
  files_read: {
    description: "Baca berkas workspace.", props: { path: s("path") }, required: ["path"],
    run: async (a) => text(await call("/files/read", "POST", { path: str(a, "path") })),
  },
  files_write: {
    description: "Tulis berkas workspace.", props: { path: s("path"), contents: s("isi"), append: { type: "boolean" } }, required: ["path", "contents"],
    run: async (a) => {
      if (typeof a.contents !== "string") throw new Error("argumen 'contents' wajib (string)");
      return text(await call("/files/write", "POST", { path: str(a, "path"), contents: a.contents, append: a.append === true }));
    },
  },
};

const listing = () =>
  Object.entries(tools).map(([name, t]) => ({
    name,
    description: t.description,
    inputSchema: { type: "object", properties: t.props ?? {}, required: t.required ?? [] },
  }));

export async function rpc(msg: Json): Promise<Json | null> {
  const { id, method, params } = msg as { id?: unknown; method?: string; params?: Json };
  if (id === undefined) return null; // notifikasi (mis. notifications/initialized)
  const ok = (result: unknown) => ({ jsonrpc: "2.0", id, result });
  const fail = (code: number, message: string) => ({ jsonrpc: "2.0", id, error: { code, message } });
  switch (method) {
    case "initialize":
      return ok({ protocolVersion: (params?.protocolVersion as string) ?? "2025-03-26", capabilities: { tools: {} }, serverInfo: { name: `computer-${BOT}`, version: "0.1.0" } });
    case "ping":
      return ok({});
    case "tools/list":
      return ok({ tools: listing() });
    case "tools/call": {
      const tool = tools[String(params?.name)];
      if (!tool) return fail(-32602, `tool tidak dikenal: ${params?.name}`);
      try {
        return ok({ content: await tool.run((params?.arguments as Json) ?? {}) });
      } catch (e) {
        return ok({ isError: true, content: text(e instanceof Error ? e.message : String(e)) });
      }
    }
    default:
      return fail(-32601, `method tidak didukung: ${method}`);
  }
}

// Egress policy: Chromium hanya boleh ke domain yang diizinkan (pagar sebenarnya, bukan cuma navigate).
// Daftar kosong = tidak ada jaringan sama sekali.
export const egressPolicy = (allowed = ALLOWED) =>
  allowed.includes("*") ? { mode: "allow_all", rules: [] }
    : allowed.length === 0 ? { mode: "deny_all", rules: [] }
    : { mode: "allowlist_only", rules: allowed.map((value) => ({ type: "domain", value })) };

// OpenBot menyimpan policy hanya di memori: komputer yang restart menolak semua koneksi sampai
// policy dikirim lagi. Maka dikirim ulang berkala (PUT idempoten), bukan sekali saat start.
let egressOk: boolean | undefined;
async function pushEgress() {
  const policy = egressPolicy();
  try {
    await call("/egress-policy", "PUT", { policy });
    if (egressOk !== true) console.log(`egress policy terpasang: ${policy.mode} (${ALLOWED.length} domain)`);
    egressOk = true;
  } catch (e) {
    if (egressOk !== false) console.error(`egress policy belum terpasang (komputer menolak semua koneksi sampai berhasil): ${e}`);
    egressOk = false;
  }
}

if (import.meta.main) {
  if (!TOKEN || !MCP_TOKEN) throw new Error("COMPUTER_TOKEN dan MCP_TOKEN wajib");
  if (TOKEN === MCP_TOKEN) throw new Error("MCP_TOKEN harus berbeda dari COMPUTER_TOKEN");
  void pushEgress();
  setInterval(pushEgress, EGRESS_REFRESH_MS);
  Bun.serve({
    port: PORT,
    async fetch(req) {
      const url = new URL(req.url);
      if (url.pathname === "/health") return new Response("ok");
      if (req.headers.get("authorization") !== `Bearer ${MCP_TOKEN}`) return new Response("unauthorized", { status: 401 });
      if (url.pathname !== "/mcp" || req.method !== "POST") return new Response("method not allowed", { status: 405 });
      const body = await req.json().catch(() => null);
      if (!body || typeof body !== "object") return Response.json({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse error" } }, { status: 400 });
      const batch = Array.isArray(body) ? body : [body];
      const out = (await Promise.all(batch.map((m) => rpc(m as Json)))).filter(Boolean);
      return out.length ? Response.json(Array.isArray(body) ? out : out[0]) : new Response(null, { status: 202 });
    },
  });
  console.log(`MCP computer-${BOT} di :${PORT}/mcp -> ${COMPUTER}`);
}
