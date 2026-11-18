"use client";

import { CalendarDays, CircleAlert, ImageIcon, Layers, Recycle, Target, Timer } from "lucide-react";
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
    { icon: ImageIcon, label: "Tên file", value: <strong className="detail-filename" title={result.file_name}>{result.file_name}</strong> },
    { icon: Recycle, label: "Loại rác", value: <WasteBadge value={result.waste_type} /> },
    ...predictionGates(result).map(({ label, value, threshold, passed }) => ({
      icon: Target,
      label,
      value: <span><strong>{formatGateReading(value, threshold)}</strong> · {passed ? "Đạt" : "Chưa đạt"}</span>,
    })),
    { icon: Layers, label: "Luồng xử lý", value: <PipelineBadge value={result.pipeline_type} /> },
    { icon: CalendarDays, label: "Thời điểm dự đoán", value: <time dateTime={result.created_at}>{formatDate(result.created_at)}</time> },
    ...(recordedTime == null ? [] : [{
      icon: Timer,
      label: processingTime == null ? "Thời gian suy luận và XAI" : "Thời gian xử lý",
      value: <strong>{formatDuration(recordedTime)}</strong>,
    }]),
    { icon: Target, label: "Điểm an toàn kết hợp", value: <span>{result.composite_score == null ? "—" : percent(result.composite_score)}</span> },
    { icon: CircleAlert, label: "Trạng thái", value: <StatusBadge value={result.status} /> },
  ];
  return <div className="prediction-details">
    <PredictionImages
      key={result.id}
      original={result.image_url || preview}
      heatmap={result.xai_overlay_url}
      energy={result.xai_energy_overlay_url}
    />
    {result.is_mock && <p className="mock-label"><span className="badge tone-amber">Kết quả mô phỏng</span></p>}
    <dl className="details-list">
      {details.map(({ icon: Icon, label, value }) => <div className="detail-row" key={label}>
        <dt><Icon aria-hidden />{label}:</dt><dd>{value}</dd>
      </div>)}
    </dl>
    <Notice><strong>Gợi ý:</strong> {result.suggestion}</Notice>
  </div>;
}

