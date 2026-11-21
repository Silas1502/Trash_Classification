"use client";

import { CalendarDays, ImageIcon, Target, Timer } from "lucide-react";
import { PredictionComparison } from "@/components/classify/PredictionComparison";
import { Notice, PipelineBadge, StatusBadge, WasteBadge } from "@/components/ui/Primitives";
import { PredictionImages } from "@/components/ui/PredictionImages";
import { formatGateReading, predictionGates } from "@/lib/predictionGates";
import { formatDate, formatDuration, percent } from "@/lib/utils";
import type { HistoryItem, PredictionResponse } from "@/types";

export function PredictionDetails({ result, preview }: { result: PredictionResponse | HistoryItem; preview?: string }) {
  const metadata = "metadata" in result ? result.metadata : undefined;
  const processingTime = result.processing_time_ms ?? metadata?.processing_time_ms;
  const recordedTime = processingTime ?? (metadata && metadata.inference_time_ms + metadata.xai_time_ms);
  const details = [
    { icon: Target, label: "Điểm an toàn kết hợp", value: <span>{result.composite_score == null ? "—" : percent(result.composite_score)}</span> },
    { icon: CalendarDays, label: "Thời điểm phân loại", value: <time dateTime={result.created_at}>{formatDate(result.created_at)}</time> },
    ...(recordedTime == null ? [] : [{
      icon: Timer,
      label: processingTime == null ? "Thời gian suy luận và XAI" : "Thời gian xử lý",
      value: <strong>{formatDuration(recordedTime)}</strong>,
    }]),
    { icon: ImageIcon, label: "Tên tệp", value: <strong className="detail-filename" title={result.file_name}>{result.file_name}</strong> },
  ];
  return <div className="prediction-details">
    <div className="prediction-detail-gallery">
      <PredictionImages
        key={result.id}
        original={result.image_url || preview}
        heatmap={result.xai_overlay_url}
        energy={result.xai_energy_overlay_url}
        zoomable
      />
    </div>
    <section className="prediction-detail-results" aria-label="Kết quả phân loại">
      <div className="prediction-detail-summary">
        <div className="prediction-detail-class">
          <span>Loại rác</span>
          <WasteBadge value={result.waste_type} />
        </div>
        <div className="prediction-detail-badges">
          <PipelineBadge value={result.pipeline_type} />
          <StatusBadge value={result.status} />
          {result.is_mock && <span className="badge tone-amber">Kết quả mô phỏng</span>}
        </div>
      </div>
      <dl className="prediction-detail-gates">
        {predictionGates(result).map(({ label, value, threshold, passed }) => <div key={label}>
          <dt>{label}</dt>
          <dd><strong>{formatGateReading(value, threshold)}</strong>
            <span className={`badge ${passed ? "tone-green" : "tone-amber"}`}>{passed ? "Đạt" : "Chưa đạt"}</span>
          </dd>
        </div>)}
      </dl>
      <dl className="details-list">
        {details.map(({ icon: Icon, label, value }) => <div className="detail-row" key={label}>
          <dt><Icon aria-hidden />{label}</dt><dd>{value}</dd>
        </div>)}
      </dl>
      <PredictionComparison result={result} ranked={result.top_predictions ?? metadata?.top_predictions} />
      <Notice><strong>Gợi ý:</strong> {result.suggestion}</Notice>
    </section>
  </div>;
}
