import { Notice } from "@/components/ui/Primitives";
import { percent } from "@/lib/utils";
import type { PredictionResponse, RankedPrediction } from "@/types";

export function PredictionComparison({ result, ranked = result.top_predictions }: {
  result: PredictionResponse; ranked?: [RankedPrediction, RankedPrediction] | null;
}) {
  const failed = [
    !result.confidence_gate_passed && "độ tin cậy",
    !result.margin_gate_passed && "biên khoảng cách",
  ].filter(Boolean);

  return <>
    {ranked && <div className="prediction-comparison">
      <strong>Hai lớp có xác suất cao nhất</strong>
      <ol>
        {ranked.map(({ waste_type, probability }, index) => <li key={index}>
          {waste_type} <strong>{percent(probability)}</strong>
        </li>)}
      </ol>
      <span>Chênh lệch {result.margin.toFixed(1)} điểm phần trăm</span>
    </div>}
    {!result.is_mock && result.pipeline_type === "Thủ công" && failed.length > 0 &&
      <Notice><strong>Cần kiểm tra:</strong> {failed.join(" và ")} chưa đạt ngưỡng.</Notice>}
  </>;
}
