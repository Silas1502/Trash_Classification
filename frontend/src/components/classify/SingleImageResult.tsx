import { ChartNoAxesColumnIncreasing, Layers, Recycle, Target } from "lucide-react";
import { Empty, Notice, PanelTitle, PipelineBadge, ProgressBar, Skeleton, StatusBadge } from "@/components/ui/Primitives";
import { PredictionImages } from "@/components/ui/PredictionImages";
import { formatGateReading, predictionGates } from "@/lib/predictionGates";
import { formatDuration } from "@/lib/utils";
import type { PredictionResponse } from "@/types";

export default function SingleImageResult({ result, busy }: { result?: PredictionResponse; busy: boolean }) {
  return <section className="panel classify-card result-panel" aria-busy={busy}>
    <PanelTitle icon={ChartNoAxesColumnIncreasing}>Kết quả dự đoán</PanelTitle>
    {busy ? <Skeleton /> : result ? <>
      <div className="result-hero">
        <span className="hero-icon"><Recycle aria-hidden /></span>
        <div className="hero-label">Loại rác: <strong>{result.waste_type}</strong></div>
        <StatusBadge value={result.status} />
      </div>
      <div className="pipeline-line">
        <span>Luồng xử lý:</span>
        <PipelineBadge value={result.pipeline_type} />
        {result.is_mock && <span className="badge tone-amber">Mô phỏng</span>}
      </div>
      {result.processing_time_ms != null && <div className="pipeline-line">
        <span>Thời gian xử lý:</span> <strong>{formatDuration(result.processing_time_ms)}</strong>
      </div>}
      <div className="metrics">
        {predictionGates(result).map(({ label, value, threshold, passed }) => <div className="metric" key={label}>
          <Layers aria-hidden />
          <div>
            <div className="metric-label">
              <span>{label}:</span>
              <strong>{formatGateReading(value, threshold)}</strong>
              <span className={"badge " + (passed ? "tone-green" : "tone-amber")}>{passed ? "Đạt" : "Chưa đạt"}</span>
            </div>
            <div className="progress-line"><ProgressBar label={label} value={value} /></div>
          </div>
        </div>)}
      </div>
      <Notice><strong>Gợi ý:</strong> {result.suggestion}</Notice>
    </> : <Empty icon={Target} title="Chưa có kết quả dự đoán">Chọn một ảnh và bấm “Bắt đầu dự đoán” để xem loại rác và độ tin cậy.</Empty>}
  </section>;
}

export function SingleImageXai({ result, preview }: { result: PredictionResponse; preview?: string }) {
  return <section className="panel xai-panel">
    <PanelTitle icon={Layers}>Kết quả XAI</PanelTitle>
    <PredictionImages
      original={result.image_url || preview}
      heatmap={result.xai_overlay_url}
      energy={result.xai_energy_overlay_url}
      comparison
    />
  </section>;
}
