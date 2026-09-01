/**
 * Where the API lives, resolved from the browser rather than baked in.
 *
 * `NEXT_PUBLIC_API_BASE_URL` wins when it is set — that is how a deployment points the
 * app at its real API host.
 *
 * When it is unset the fallback used to be a literal `http://localhost:8000`, which
 * quietly assumed the browser and the API were the same machine. They are not when the
 * page is opened on a phone: `localhost` is then the *phone*, so every call failed and
 * the whole citizen journey was untestable on the one device this project is built for.
 * That is why OPEN_ITEMS OI-29 stayed open — not because nobody tried, but because it
 * could not work.
 *
 * So the fallback follows the page: whatever host served this HTML also serves the API,
 * on port 8000. Open http://192.168.1.9:3000 on a handset and it calls
 * http://192.168.1.9:8000 — no configuration, no rebuild.
 *
 * During server rendering there is no `window`. Every caller fetches from an effect or an
 * event handler, so the literal below is only ever a placeholder for a request that is
 * never made from the server.
 */
const API_PORT = "8000";
const API_PATH = "/api/v1";

export function apiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured) return configured;

  if (typeof window === "undefined") {
    // Server render: nothing fetches from here, so this value is never dialled.
    return `http://localhost:${API_PORT}${API_PATH}`;
  }

  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:${API_PORT}${API_PATH}`;
}

/** The origin only, for endpoints outside the versioned prefix such as `/readyz`. */
export function apiOrigin(): string {
  return apiBase().replace(API_PATH, "");
}
