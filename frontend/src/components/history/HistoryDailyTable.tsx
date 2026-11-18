"use client";

import { useEffect, useState, type FormEvent } from "react";
import { LoaderCircle } from "lucide-react";
import { Pagination } from "@/components/history/HistoryTable";
import { Button, Skeleton } from "@/components/ui/Primitives";
import { errorMessage } from "@/services/api";
import { getHistoryDaily } from "@/services/historyService";
import type { HistoryDailyResponse } from "@/types";

function recentDates() {
  const vietnamNow = Date.now() + 7 * 3600_000;
  return {
    start: new Date(vietnamNow - 6 * 86400_000).toISOString().slice(0, 10),
    end: new Date(vietnamNow).toISOString().slice(0, 10),
  };
}

function displayDate(value: string) {
  return value.split("-").reverse().join("/");
}

export default function HistoryDailyTable() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState({ start: "", end: "" });
  const [range, setRange] = useState<{ start: string; end: string }>();
  const [page, setPage] = useState(1);
  const [data, setData] = useState<HistoryDailyResponse>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const dates = recentDates();
    setDraft(dates);
    setRange(dates);
  }, []);

  useEffect(() => {
    if (!open || !range) return;
    const controller = new AbortController();
    setLoading(true);
    setError(undefined);
    setData(undefined);
    getHistoryDaily(range.start, range.end, page, controller.signal)
      .then(value => { if (!controller.signal.aborted) setData(value); })
      .catch(error => { if (!controller.signal.aborted) setError(errorMessage(error, "Không thể tải số liệu theo ngày.")); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [open, range, page, retry]);

  function apply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.start || !draft.end || draft.start > draft.end) {
      setError("Hãy chọn khoảng ngày hợp lệ.");
      return;
    }
    setPage(1);
    setRange({ ...draft });
  }

  const offset = (page - 1) * 5;
  return <details className="chart-data" onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>Xem số liệu theo ngày</summary>
    <form className="daily-range-form" onSubmit={apply}>
      <label>Từ ngày<input className="input-wrap" type="date" required value={draft.start} max={draft.end}
        onChange={event => setDraft(value => ({ ...value, start: event.target.value }))} /></label>
      <label>Đến ngày<input className="input-wrap" type="date" required value={draft.end} min={draft.start}
        onChange={event => setDraft(value => ({ ...value, end: event.target.value }))} /></label>
      <Button type="submit" disabled={loading || !range}>
        {loading && <LoaderCircle className="spin" aria-hidden />}Xem số liệu
      </Button>
    </form>
    {loading ? <Skeleton rows={5} /> : error ? <div className="chart-error">
      <p role="alert">{error}</p>
      <Button variant="outline" onClick={() => setRetry(value => value + 1)}>Thử tải lại số liệu</Button>
    </div> : data && <>
      <div className="chart-scroll"><table className="data-table" aria-label="Số liệu dự đoán theo ngày">
        <thead><tr><th scope="col">Ngày</th><th scope="col">Tổng số ảnh</th><th scope="col">Tự động</th><th scope="col">Thủ công</th></tr></thead>
        <tbody>{data.points.map(point => <tr key={point.start_date}>
          <th scope="row">{displayDate(point.start_date)}</th>
          <td>{point.total}</td><td>{point.automatic}</td><td>{point.needs_review}</td>
        </tr>)}</tbody>
      </table></div>
      <div className="daily-table-footer">
        <span>{data.points.length ? `Ngày ${offset + 1}–${offset + data.points.length} trên ${data.total_days} ngày` : "Không có ngày trong trang này"}</span>
        <Pagination page={data.page} last={data.total_pages} go={setPage} label="Phân trang số liệu theo ngày" />
      </div>
    </>}
  </details>;
}
