import { ChevronLeft, ChevronRight, List } from "lucide-react";
import { Button, Empty, Notice, PanelTitle, PipelineBadge, Skeleton, WasteBadge } from "@/components/ui/Primitives";
import { formatDate, percent } from "@/lib/utils";
import type { HistoryItem, HistoryQueryResponse } from "@/types";

export function Pagination({ page, last, go, label = "Phân trang lịch sử" }: {
  page: number; last: number; go: (page: number) => void; label?: string;
}) {
  const pages = [...new Set([1, page - 1, page, page + 1, last, ...(page < 3 ? [2, 3] : [])])]
    .filter(item => item >= 1 && item <= last).sort((a, b) => a - b);
  return <nav className="pagination" aria-label={label}>
    <Button variant="outline" aria-label="Trang trước" disabled={page <= 1} onClick={() => go(page - 1)}><ChevronLeft aria-hidden /></Button>
    {pages.map((item, index) => <span className="page-number" key={item}>
      {index > 0 && item - pages[index - 1] > 1 && <span className="page-gap">…</span>}
      <Button variant={item === page ? "primary" : "outline"} aria-label={"Trang " + item} aria-current={item === page ? "page" : undefined} onClick={() => go(item)}>{item}</Button>
    </span>)}
    <Button variant="outline" aria-label="Trang tiếp theo" disabled={page >= last} onClick={() => go(page + 1)}><ChevronRight aria-hidden /></Button>
  </nav>;
}

export default function HistoryTable({ data, loading, error, activeId, onSelect, onPage, onRetry }: {
  data?: HistoryQueryResponse; loading: boolean; error?: string; activeId?: string;
  onSelect: (item: HistoryItem) => void; onPage: (page: number) => void; onRetry: () => void;
}) {
  const offset = data ? (data.page - 1) * data.limit : 0;
  return <section className="panel history-table-panel" aria-busy={loading}>
    <div className="panel-head"><PanelTitle icon={List}>Danh sách lịch sử</PanelTitle>
      {data && <span className="record-count">{data.total} bản ghi</span>}
    </div>
    <div className="table-frame">
      <table className="data-table history-table">
        <thead><tr><th scope="col">STT</th><th scope="col">Tên file</th><th scope="col">Loại rác</th><th scope="col">Độ tin cậy</th><th scope="col">Luồng xử lý</th><th scope="col">Thời điểm phân loại</th></tr></thead>
        <tbody>{!loading && !error && data?.items.map((item, index) => <tr className={activeId === item.id ? "selected" : undefined}
          key={item.id} onClick={event => {
            event.currentTarget.querySelector<HTMLButtonElement>(".row-trigger")?.focus({ preventScroll: true });
            onSelect(item);
          }}>
          <td>{offset + index + 1}</td>
          <td><button className="row-trigger" type="button" aria-haspopup="dialog" title={item.file_name}
            onClick={event => { event.stopPropagation(); onSelect(item); }}>{item.file_name}</button></td>
          <td><WasteBadge value={item.waste_type} /></td>
          <td>{percent(item.confidence)}</td><td><PipelineBadge value={item.pipeline_type} /></td>
          <td><time dateTime={item.created_at}>{formatDate(item.created_at)}</time></td>
        </tr>)}</tbody>
      </table>
      {loading ? <Skeleton rows={5} /> : error ? <Empty icon={List} title="Không tải được lịch sử">
        {error}<br /><Button variant="outline" onClick={onRetry}>Thử lại</Button>
      </Empty> : (!data?.items.length && <Empty icon={List} title="Không có kết quả">Thử thay đổi bộ lọc hoặc phân loại ảnh mới.</Empty>)}
    </div>
    {Boolean(data?.items.length) && <Notice>Nhấn vào một dòng để xem chi tiết kết quả.</Notice>}
    {data && !loading && !error && <div className="history-footer">
      <span>{data.items.length ? "Hiển thị " + (offset + 1) + "–" + (offset + data.items.length) + " trên " + data.total + " kết quả" : "0 kết quả"}</span>
      <Pagination page={data.page} last={Math.max(1, data.total_pages)} go={onPage} />
    </div>}
  </section>;
}
