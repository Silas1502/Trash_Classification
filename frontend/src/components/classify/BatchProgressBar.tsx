import { ChartNoAxesColumnIncreasing, CircleCheck, Clock3, ImageIcon, Play, RotateCcw, Square, Target } from "lucide-react";
import { Button, PanelTitle, ProgressBar } from "@/components/ui/Primitives";

export default function BatchProgressBar({ total, processed, failed, busy, retryable, hasProcessedUploads, onStart, onStop, onReset }: {
  total: number; processed: number; failed: number; busy: boolean; retryable: boolean; hasProcessedUploads: boolean;
  onStart: () => void; onStop: () => void; onReset: () => void;
}) {
  const progress = total ? Math.round(processed / total * 100) : 0;
  let startLabel = "Bắt đầu xử lý";
  if (busy) startLabel = "Đang xử lý…";
  else if (total > 0 && total === processed) startLabel = total === failed ? "Đã kiểm tra xong" : "Đã xử lý xong";
  else if (retryable) startLabel = "Thử lại";
  else if (hasProcessedUploads) startLabel = "Tiếp tục xử lý";
  const cards = [
    { icon: ImageIcon, label: "Tổng số tệp", value: total, tone: "blue" },
    { icon: CircleCheck, label: "Đã xử lý", value: processed, tone: "green" },
    { icon: Clock3, label: "Đang chờ", value: total - processed, tone: "sand" },
    { icon: Target, label: "Tỷ lệ hoàn thành", value: progress + "%", tone: "blue" },
  ];
  return <section className="panel classify-card batch-progress">
    <PanelTitle icon={ChartNoAxesColumnIncreasing}>Tiến độ xử lý</PanelTitle>
    <div className="metric-cards" aria-live="polite">
      {cards.map(({ icon: Icon, label, value, tone }) => <div className={"metric-card tone-" + tone} key={label}>
        <Icon aria-hidden /><div><span>{label}:</span><strong>{value}</strong></div>
      </div>)}
    </div>
    <div className="progress-line total-progress"><ProgressBar label="Tiến độ xử lý ảnh" value={progress} /><span>{progress}%</span></div>
    <div className="batch-actions">
      <Button disabled={busy || total === processed} onClick={onStart}><Play className="play-icon" aria-hidden />{startLabel}</Button>
      {total > 0 && (busy
        ? <Button variant="outline" onClick={onStop}><Square aria-hidden />Dừng</Button>
        : <Button variant="outline" onClick={onReset}><RotateCcw aria-hidden />Làm mới</Button>)}
    </div>
    {failed > 0 && <p className="failed-summary">{failed} tệp không xử lý được. Xem lý do trong bảng kết quả.</p>}
  </section>;
}
