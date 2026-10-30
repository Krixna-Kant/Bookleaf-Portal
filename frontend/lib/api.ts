import type { TokenResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function token() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function saveSession(session: TokenResponse) {
  localStorage.setItem("access_token", session.access_token);
  localStorage.setItem("refresh_token", session.refresh_token);
}

export function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshSession() {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return false;
  const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) return false;
  saveSession(await response.json());
  return true;
}

export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  const access = token();
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (response.status === 401 && retry && path !== "/api/v1/auth/login") {
    const refreshed = await refreshSession();
    if (refreshed) return api<T>(path, init, false);
    clearSession();
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.error?.message || "Request failed";
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function subscribeEvents(
  onEvent: (event: { type: string; ticket_id?: number }) => void,
  signal: AbortSignal,
) {
  const access = token();
  const response = await fetch(`${API_URL}/api/v1/events/stream`, {
    headers: access ? { Authorization: `Bearer ${access}` } : {},
    signal,
  });
  if (!response.ok || !response.body) throw new Error("Live updates unavailable");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((item) => item.startsWith("data:"));
      if (!line) continue;
      const event = JSON.parse(line.slice(5).trim());
      if (event.type !== "ping" && event.type !== "connected") onEvent(event);
    }
  }
}

export function inr(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function when(value: string | null | undefined) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
