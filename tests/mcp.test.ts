import { afterAll, beforeAll, describe, expect, test } from "bun:test";

// Agent-computer palsu: merekam request yang diteruskan sidecar.
const seen: { path: string; method: string; headers: Headers; body: any }[] = [];
const fake = Bun.serve({
  port: 0,
  async fetch(req) {
    const url = new URL(req.url);
    const body = await req.json().catch(() => null);
    seen.push({ path: url.pathname, method: req.method, headers: req.headers, body });
    if (url.pathname === "/screenshot") return Response.json({ base64: "aGk=" });
    if (url.pathname === "/click") return Response.json({ error: "ref tidak ditemukan" }, { status: 404 });
    return Response.json({ ok: true, path: url.pathname });
  },
});

process.env.COMPUTER_URL = `http://localhost:${fake.port}`;
process.env.COMPUTER_TOKEN = "tok";
process.env.MCP_TOKEN = "mcp-tok";
process.env.EGRESS_REFRESH_MS = "150";
process.env.BOT_ID = "ops-holding";
process.env.ALLOWED_DOMAINS = "example.com,*.bank.co.id";

const { hostAllowed, rpc } = await import("../computer-mcp/server.ts");
const call = (name: string, args: object = {}) =>
  rpc({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name, arguments: args } }) as Promise<any>;

afterAll(() => fake.stop(true));

describe("hostAllowed", () => {
  const A = ["example.com", "*.bank.co.id"];
  test("domain persis dan subdomain", () => {
    expect(hostAllowed("https://example.com/x", A)).toBe(true);
    expect(hostAllowed("https://a.example.com", A)).toBe(true);
    expect(hostAllowed("https://x.bank.co.id", A)).toBe(true);
  });
  test("menolak domain mirip, skema aneh, URL rusak", () => {
    expect(hostAllowed("https://evilexample.com", A)).toBe(false);
    expect(hostAllowed("https://example.com.evil.io", A)).toBe(false);
    expect(hostAllowed("file:///etc/passwd", A)).toBe(false);
    expect(hostAllowed("javascript:alert(1)", A)).toBe(false);
    expect(hostAllowed("bukan url", A)).toBe(false);
  });
  test("daftar kosong menolak semua, '*' mengizinkan", () => {
    expect(hostAllowed("https://example.com", [])).toBe(false);
    expect(hostAllowed("https://apa.saja", ["*"])).toBe(true);
  });
});

describe("rpc", () => {
  test("initialize, ping, notifikasi", async () => {
    const init: any = await rpc({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-03-26" } });
    expect(init.result.capabilities.tools).toBeDefined();
    expect(init.result.serverInfo.name).toBe("computer-ops-holding");
    expect(((await rpc({ jsonrpc: "2.0", id: 2, method: "ping" })) as any).result).toEqual({});
    expect(await rpc({ jsonrpc: "2.0", method: "notifications/initialized" })).toBeNull();
  });

  test("tools/list: tanpa tool eksekusi shell", async () => {
    const r: any = await rpc({ jsonrpc: "2.0", id: 3, method: "tools/list" });
    const names = r.result.tools.map((t: any) => t.name);
    expect(names).toContain("browser_navigate");
    expect(names).toContain("request_help");
    expect(names.some((n: string) => /exec|shell|terminal|bash/.test(n))).toBe(false);
    for (const t of r.result.tools) expect(t.inputSchema.type).toBe("object");
  });

  test("method asing -> error JSON-RPC", async () => {
    const r: any = await rpc({ jsonrpc: "2.0", id: 4, method: "foo/bar" });
    expect(r.error.code).toBe(-32601);
  });

  test("tool tidak dikenal -> error JSON-RPC", async () => {
    const r: any = await call("browser_hack");
    expect(r.error.code).toBe(-32602);
  });
});

describe("tools/call", () => {
  test("navigate ke domain terlarang diblok dan TIDAK diteruskan", async () => {
    seen.length = 0;
    const r = await call("browser_navigate", { url: "https://evil.io" });
    expect(r.result.isError).toBe(true);
    expect(r.result.content[0].text).toContain("tidak diizinkan");
    expect(seen.length).toBe(0);
  });

  test("navigate ke domain diizinkan diteruskan dengan header token + bot id", async () => {
    seen.length = 0;
    const r = await call("browser_navigate", { url: "https://example.com/a" });
    expect(r.result.isError).toBeUndefined();
    expect(seen[0].path).toBe("/navigate");
    expect(seen[0].method).toBe("POST");
    expect(seen[0].headers.get("x-openbot-computer-token")).toBe("tok");
    expect(seen[0].headers.get("x-openbot-bot-id")).toBe("ops-holding");
    expect(seen[0].body).toEqual({ url: "https://example.com/a" });
  });

  test("argumen wajib hilang -> isError, bukan crash", async () => {
    const r = await call("browser_click", {});
    expect(r.result.isError).toBe(true);
    expect(r.result.content[0].text).toContain("ref");
  });

  test("error upstream -> isError dengan pesan upstream", async () => {
    const r = await call("browser_click", { ref: "e1" });
    expect(r.result.isError).toBe(true);
    expect(r.result.content[0].text).toContain("ref tidak ditemukan");
  });

  test("snapshotId diteruskan hanya jika ada", async () => {
    seen.length = 0;
    await call("browser_type", { ref: "e2", text: "halo", snapshotId: 7 });
    expect(seen[0].body).toEqual({ ref: "e2", text: "halo", submit: false, snapshotId: 7 });
  });

  test("screenshot dikembalikan sebagai konten gambar MCP", async () => {
    const r = await call("browser_screenshot");
    expect(r.result.content[0]).toEqual({ type: "image", data: "aGk=", mimeType: "image/png" });
  });

  test("files_write tanpa contents ditolak (bukan menulis 'undefined')", async () => {
    seen.length = 0;
    const r = await call("files_write", { path: "a.txt" });
    expect(r.result.isError).toBe(true);
    expect(seen.length).toBe(0);
    await call("files_write", { path: "kosong.txt", contents: "" });
    expect(seen[0].body).toEqual({ path: "kosong.txt", contents: "", append: false });
  });

  test("request_help -> /control/request", async () => {
    seen.length = 0;
    await call("request_help", { reason: "perlu login" });
    expect(seen[0].path).toBe("/control/request");
    expect(seen[0].body).toEqual({ reason: "perlu login" });
  });
});

describe("server HTTP (subprocess)", () => {
  let proc: ReturnType<typeof Bun.spawn>;
  const port = 18700 + Math.floor(Math.random() * 500);
  const base = `http://localhost:${port}`;
  beforeAll(async () => {
    seen.length = 0;
    proc = Bun.spawn(["bun", `${import.meta.dir}/../computer-mcp/server.ts`], {
      env: { ...process.env, PORT: String(port) },
      stdout: "ignore", stderr: "ignore",
    });
    for (let i = 0; i < 50; i++) {
      try { if ((await fetch(`${base}/health`)).ok) return; } catch {}
      await Bun.sleep(100);
    }
    throw new Error("server tidak naik");
  });
  afterAll(() => proc.kill());

  const post = (body: unknown, token = "mcp-tok") =>
    fetch(`${base}/mcp`, { method: "POST", headers: { authorization: `Bearer ${token}`, "content-type": "application/json" }, body: JSON.stringify(body) });

  test("tanpa/dengan token salah -> 401; token komputer TIDAK berlaku untuk MCP", async () => {
    expect((await post({}, "salah")).status).toBe(401);
    expect((await post({}, "tok")).status).toBe(401);
    expect((await fetch(`${base}/mcp`, { method: "POST" })).status).toBe(401);
  });
  test("GET -> 405, JSON rusak -> 400", async () => {
    expect((await fetch(`${base}/mcp`, { headers: { authorization: "Bearer mcp-tok" } })).status).toBe(405);
    const bad = await fetch(`${base}/mcp`, { method: "POST", headers: { authorization: "Bearer mcp-tok" }, body: "{bukan json" });
    expect(bad.status).toBe(400);
  });
  test("tools/list lewat HTTP", async () => {
    const j: any = await (await post({ jsonrpc: "2.0", id: 1, method: "tools/list" })).json();
    expect(j.result.tools.length).toBeGreaterThan(5);
  });
  test("notifikasi -> 202", async () => {
    expect((await post({ jsonrpc: "2.0", method: "notifications/initialized" })).status).toBe(202);
  });
  test("egress policy dipasang ke computer saat start", async () => {
    let put: any;
    for (let i = 0; i < 50 && !put; i++) {
      put = seen.find((s) => s.path === "/egress-policy");
      if (!put) await Bun.sleep(100);
    }
    expect(put.method).toBe("PUT");
    expect(put.headers.get("x-openbot-computer-token")).toBe("tok");
    expect(put.body).toEqual({
      policy: { mode: "allowlist_only", rules: [{ type: "domain", value: "example.com" }, { type: "domain", value: "*.bank.co.id" }] },
    });
  });
  test("egress policy dipasang ulang berkala (komputer restart = policy di memori hilang)", async () => {
    const count = () => seen.filter((x) => x.path === "/egress-policy").length;
    const before = count();
    await Bun.sleep(500);
    expect(count()).toBeGreaterThan(before);
  });
});

describe("start-up guard", () => {
  const start = (env: Record<string, string>) =>
    Bun.spawnSync(["bun", `${import.meta.dir}/../computer-mcp/server.ts`], {
      env: { ...process.env, PORT: "0", ...env }, stdout: "pipe", stderr: "pipe", timeout: 5000,
    });
  test("menolak start bila token MCP sama dengan token komputer", () => {
    const r = start({ MCP_TOKEN: "tok", COMPUTER_TOKEN: "tok" });
    expect(r.exitCode).not.toBe(0);
    expect(r.stderr.toString()).toContain("MCP_TOKEN");
  });
  test("menolak start tanpa MCP_TOKEN", () => {
    const r = start({ MCP_TOKEN: "" });
    expect(r.exitCode).not.toBe(0);
  });
});

test("ALLOWED_DOMAINS kosong -> egress deny_all", async () => {
  const { egressPolicy } = await import("../computer-mcp/server.ts");
  expect(egressPolicy([])).toEqual({ mode: "deny_all", rules: [] });
  expect(egressPolicy(["*"])).toEqual({ mode: "allow_all", rules: [] });
  expect(egressPolicy(["a.com"])).toEqual({ mode: "allowlist_only", rules: [{ type: "domain", value: "a.com" }] });
});
