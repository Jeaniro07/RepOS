// Stand-in for @rakazo/contracts McpServerConfigInput: remote transports need an https endpoint and string headers.
export const McpServerConfigInput = {
  safeParse(input) {
    const ok = ["streamable_http", "sse"].includes(input.transport) && typeof input.endpoint === "string" &&
      /^https:\/\/[^\s/]+/.test(input.endpoint) && input.endpoint.length <= 2048 &&
      Object.values(input.headers ?? {}).every((v) => typeof v === "string");
    return ok ? { success: true, data: { ...input, headers: input.headers ?? {} } } : { success: false };
  },
};
