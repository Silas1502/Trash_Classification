import { percent } from "@/lib/utils";
import type { PredictionResponse } from "@/types";

export const gateLabels = {
  confidence: "Độ tin cậy",
  margin: "Biên khoảng cách",
};

export function predictionGates(result: PredictionResponse) {
  return [
    {
      label: gateLabels.confidence,
      value: result.confidence,
      threshold: result.checkpoint_1,
      passed: result.confidence_gate_passed,
    },
    {
      label: gateLabels.margin,
      value: result.margin,
      threshold: result.checkpoint_2,
      passed: result.margin_gate_passed,
    },
  ];
}

export function formatGateReading(value: number, threshold: number) {
  return `${percent(value)} (ngưỡng ${percent(threshold)})`;
}
