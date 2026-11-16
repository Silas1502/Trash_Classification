import axios from "axios";
import type { HealthCheckResponse } from "@/types";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
});

export async function getHealth(signal: AbortSignal) {
  const { data } = await api.get<HealthCheckResponse>("/health", { signal, timeout: 5000 });
  return data;
}

export function errorMessage(error: unknown, fallback: string) {
  if (!axios.isAxiosError<{ detail?: string | { message?: string }; error?: { message?: string }; message?: string }>(error)) return fallback;
  const data = error.response?.data;
  const detail = data?.detail;
  return data?.error?.message || data?.message ||
    (typeof detail === "string" ? detail : detail?.message) ||
    (error.code === "ERR_NETWORK" ? "Không thể kết nối với máy chủ AI." : fallback);
}
