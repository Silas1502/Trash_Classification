import { downloadBlob } from "@/lib/utils";
import { api } from "@/services/api";
import type { HistoryDailyResponse, HistoryFilters, HistoryItem, HistoryQueryResponse, HistoryTrendPeriod, HistoryTrendsResponse } from "@/types";

export async function getHistory(filters: HistoryFilters, page: number, limit: number, signal: AbortSignal) {
  return (await api.get<HistoryQueryResponse>("/history", { params: { ...filters, page, limit }, signal })).data;
}

export async function getHistoryDetail(id: string, signal: AbortSignal) {
  return (await api.get<HistoryItem>("/history/" + encodeURIComponent(id), { signal })).data;
}

export async function getHistoryTrends(period: HistoryTrendPeriod, signal: AbortSignal) {
  const { data } = await api.get<HistoryTrendsResponse>("/history/trends", {
    params: { period }, signal, timeout: 15000,
  });
  return data;
}

export async function getHistoryDaily(startDate: string, endDate: string, page: number, signal: AbortSignal) {
  const { data } = await api.get<HistoryDailyResponse>("/history/daily", {
    params: { start_date: startDate, end_date: endDate, page }, signal, timeout: 15000,
  });
  return data;
}

export async function exportHistory(filters: HistoryFilters) {
  const { data } = await api.get<Blob>("/history/export", { params: filters, responseType: "blob" });
  downloadBlob(data, "trash_classification_history.csv");
}
