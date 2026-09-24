import { getToken } from "../auth/storage";
import { environment } from "../config/environment";

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${environment.apiBaseUrl}${path}`, { ...init, headers });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail ?? `Request failed (${response.status})`);
  return data as T;
}


export async function openNotificationSocket(
  onMessage: (message: unknown) => void,
  onError?: () => void,
): Promise<() => void> {
  const { getToken } = await import("../auth/storage");
  const { environment } = await import("../config/environment");
  const token = await getToken();
  if (!token) return () => {};

  const base = environment.apiBaseUrl.replace(/\/api\/v1\/?$/, "");
  const socket = new WebSocket(`${base.replace(/^http/, "ws")}/ws/notifications?token=${encodeURIComponent(token)}`);
  socket.onmessage = (event) => {
    try { onMessage(JSON.parse(event.data)); } catch { /* ignore malformed events */ }
  };
  socket.onerror = () => onError?.();
  socket.onopen = () => socket.send("subscribe");
  return () => socket.close();
}
