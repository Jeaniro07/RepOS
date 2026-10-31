// Same rule as Rakazo connector-http.ts: credentials never in the endpoint query.
export function assertNoSensitiveQuery(value) {
  const url = new URL(value);
  const name = [...url.searchParams.keys()].find((n) => /(auth|credential|key|password|secret|token)/i.test(n));
  if (name) throw new Error(`Connector URL must put ${name} in the encrypted credential field`);
}
