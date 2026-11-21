"use client";

import { useEffect, useMemo, useState } from "react";
import HistoryFilterBar, { initialFilters, type FilterValues } from "@/components/history/HistoryFilterBar";
import HistoryTable from "@/components/history/HistoryTable";
import { PredictionDetails } from "@/components/history/PredictionDetails";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Primitives";
import { useToast } from "@/components/ui/Toast";
import { errorMessage } from "@/services/api";
import { exportHistory, getHistory, getHistoryDetail } from "@/services/historyService";
import type { HistoryFilters, HistoryItem, HistoryQueryResponse } from "@/types";

const pageSize = 10;
function toQuery({ search, waste, pipeline, range }: FilterValues): HistoryFilters {
  const days = range === "month" ? 29 : range === "week" ? 6 : 0;
  // Align date filters with the UTC+07:00 dates displayed in the table.
  const day = 86400_000;
  const zoneOffset = 7 * 3600_000;
  const today = Math.floor((Date.now() + zoneOffset) / day) * day - zoneOffset;
  return { search: search.trim() || undefined, waste_type: waste || undefined, pipeline_type: pipeline || undefined,
    start_date: range ? new Date(today - days * day).toISOString() : undefined,
    end_date: range ? new Date(today + day - 1).toISOString() : undefined };
}

export default function HistoryPage() {
  const [filters, setFilters] = useState(initialFilters);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<HistoryQueryResponse>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [selected, setSelected] = useState<HistoryItem>();
  const [detail, setDetail] = useState<{ item?: HistoryItem; error?: string; loading: boolean }>({ loading: false });
  const [exporting, setExporting] = useState(false);
  const notify = useToast();
  const { waste, pipeline, range } = filters;
  const query = useMemo(() => toQuery({ search, waste, pipeline, range }), [search, waste, pipeline, range]);

  useEffect(() => {
    if (search === filters.search) return;
    const timer = window.setTimeout(() => { setSearch(filters.search); setPage(1); }, 260);
    return () => window.clearTimeout(timer);
  }, [filters.search, search]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(undefined);
    getHistory(query, page, pageSize, controller.signal)
      .then(value => { if (!controller.signal.aborted) setData(value); })
      .catch(error => { if (!controller.signal.aborted) { setData(undefined); setError(errorMessage(error, "Vui lòng thử lại sau.")); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [query, page, retry]);

  const selectedId = selected?.id;
  useEffect(() => {
    if (!selectedId) return;
    const controller = new AbortController();
    getHistoryDetail(selectedId, controller.signal)
      .then(item => { if (!controller.signal.aborted) setDetail({ item, loading: false }); })
      .catch(error => { if (!controller.signal.aborted) setDetail({ error: errorMessage(error, "Không tải được chi tiết."), loading: false }); });
    return () => controller.abort();
  }, [selectedId]);

  async function download() {
    setExporting(true);
    try {
      await exportHistory(toQuery(filters));
      notify("Đã xuất lịch sử thành tệp CSV.", "success");
    } catch (error) {
      notify(errorMessage(error, "Không thể xuất lịch sử. Vui lòng thử lại."), "error");
    } finally { setExporting(false); }
  }

  return <div className="page history-page">
    <header className="page-header"><h1>Lịch sử phân loại</h1><p>Tra cứu kết quả phân loại rác đã thực hiện</p></header>
    <HistoryFilterBar value={filters} onChange={value => { setFilters(value); if (value.waste !== waste || value.pipeline !== pipeline || value.range !== range) setPage(1); setSelected(undefined); }}
      onExport={download} exporting={exporting} />
    <HistoryTable data={data} loading={loading} error={error} activeId={selectedId}
      onSelect={item => { setDetail({ loading: true }); setSelected(item); }}
      onPage={setPage} onRetry={() => setRetry(retry + 1)} />
    {selected && (
      <Modal title="Chi tiết phân loại" wide onClose={() => setSelected(undefined)}>
        <div className="history-modal-detail" aria-busy={detail.loading}>
          {detail.loading && <Skeleton rows={1} />}
          {detail.error && <p className="inline-error" role="alert">{detail.error} Đang hiển thị thông tin từ bảng lịch sử.</p>}
          <PredictionDetails result={detail.item ?? selected} />
        </div>
      </Modal>
    )}
  </div>;
}
