import { api } from "@/services/api";
import type { HistoryFilters, HistoryItem, HistoryQueryResponse } from "@/types";

export async function getHistory(filters: HistoryFilters, page: number, limit: number, signal: AbortSignal) {
  return (await api.get<HistoryQueryResponse>("/history", { params: { ...filters, page, limit }, signal })).data;
}

export async function getHistoryDetail(id: string, signal: AbortSignal) {
  return (await api.get<HistoryItem>("/history/" + encodeURIComponent(id), { signal })).data;
}

export async function exportHistory(filters: HistoryFilters) {
  const { data } = await api.get<Blob>("/history/export", { params: filters, responseType: "blob" });
  const url = URL.createObjectURL(data);
  const link = document.createElement("a");
  link.href = url;
  link.download = "trash_classification_history.csv";
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
