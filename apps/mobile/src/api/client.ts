import { getToken } from "../auth/storage";
import { environment } from "../config/environment";

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${environment.apiBaseUrl}${path}`, { ...init, headers });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail ?? `Request failed (${response.status})`);
  return data as T;
}
