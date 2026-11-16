"use client";

import { CalendarDays, CircleAlert, ImageIcon, Layers, Recycle, Target } from "lucide-react";
import { Notice, PipelineBadge, StatusBadge, WasteBadge } from "@/components/ui/Primitives";
import { PredictionImages } from "@/components/ui/PredictionImages";
import { formatGateReading, predictionGates } from "@/lib/predictionGates";
import { formatDate, percent } from "@/lib/utils";
import type { PredictionResponse } from "@/types";

export function PredictionDetails({ result, preview }: { result: PredictionResponse; preview?: string }) {
  const details = [
    { icon: ImageIcon, label: "Tên file", value: <strong className="detail-filename" title={result.file_name}>{result.file_name}</strong> },
    { icon: Recycle, label: "Loại rác", value: <WasteBadge value={result.waste_type} /> },
    ...predictionGates(result).map(({ label, value, threshold, passed }) => ({
      icon: Target,
      label,
      value: <span><strong>{formatGateReading(value, threshold)}</strong> · {passed ? "Đạt" : "Chưa đạt"}</span>,
    })),
    { icon: Layers, label: "Luồng xử lý", value: <PipelineBadge value={result.pipeline_type} /> },
    { icon: CalendarDays, label: "Thời gian dự đoán", value: <time dateTime={result.created_at}>{formatDate(result.created_at)}</time> },
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

