// ==============================
// RelayDesk frontend configuration
// ==============================

/**
 * Base REST API URL — uses environment if provided,
 * falls back to localhost:8000 for local development.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE ??
  "http://localhost:8000";

/**
 * WebSocket host — resolves either from NEXT_PUBLIC_WS_HOST or same localhost.
 */
export const WS_HOST =
  process.env.NEXT_PUBLIC_WS_HOST ??
  (process.env.NEXT_PUBLIC_WS_URL
    ? process.env.NEXT_PUBLIC_WS_URL.replace(/^wss?:\/\//, "")
    : "localhost:8000");

/**
 * Helper for runtime-safe WebSocket base URL.
 */
export const resolveWebSocketBase = (): string => {
  if (typeof window === "undefined") {
    return `ws://localhost:8000`;
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const wsHost = WS_HOST;
  return `${protocol}://${wsHost}`;
};
