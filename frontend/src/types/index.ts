export const modelWasteTypes = ["Nhựa", "Giấy", "Kim loại", "Thủy tinh"] as const;
export const wasteTypes = [...modelWasteTypes, "Hữu cơ", "Khác"] as const;
export const pipelineTypes = ["Tự động", "Thủ công"] as const;
export type WasteType = typeof wasteTypes[number];
export type PipelineType = typeof pipelineTypes[number] | "Chưa thẩm định";

export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "error";
  model: "pending" | "loaded" | "mock" | "error";
  database: "connected" | "disconnected" | "checking" | "not_configured";
  storage: "reachable" | "unreachable" | "checking" | "not_configured";
}

export interface RankedPrediction {
  waste_type: WasteType;
  probability: number;
}

export interface PredictionResponse {
  id: string;
  file_name: string;
  image_url: string | null;
  xai_overlay_url: string | null;
  xai_energy_overlay_url?: string | null;
  waste_type: WasteType;
  confidence: number;
  margin: number;
  checkpoint_1: number;
  checkpoint_2: number;
  confidence_gate_passed: boolean;
  margin_gate_passed: boolean;
  composite_score: number | null;
  tta_stability: number | null;
  decision_tier: string | null;
  decision: "Tu_Dong_Gap" | "Chuyen_Khay_Thu_Cong" | "Khong_Tham_Dinh" | null;
  is_mock: boolean;
  pipeline_type: PipelineType;
  status: "Thành công" | "Cần kiểm tra" | "Chưa thẩm định";
  reason: string | null;
  suggestion: string;
  created_at: string;
  processing_time_ms?: number;
  top_predictions?: [RankedPrediction, RankedPrediction];
}

export interface HistoryItem extends PredictionResponse {
  metadata: {
    file_size: number;
    mime_type: string;
    inference_time_ms: number;
    xai_time_ms: number;
    processing_time_ms?: number | null;
    top_predictions?: [RankedPrediction, RankedPrediction] | null;
    model_version: string;
    tta_views: 1 | 5;
    crop_box: [number, number, number, number];
    crop_strategy: "subject_center" | "image_center";
  };
}

export interface HistoryFilters {
  waste_type?: WasteType;
  pipeline_type?: PipelineType;
  search?: string;
  start_date?: string;
  end_date?: string;
}

export interface HistoryQueryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export type HistoryTrendPeriod = "today" | "week" | "month" | "quarter";

export interface HistoryTrendPoint {
  start_date: string;
  end_date: string;
  total: number;
  automatic: number;
  needs_review: number;
  start_at?: string | null;
  end_at?: string | null;
  is_future?: boolean;
}

export interface HistoryTrendsResponse {
  unit: "hour" | "day" | "week";
  points: HistoryTrendPoint[];
  by_waste_type: Record<WasteType, number>;
}

export interface HistoryDailyResponse {
  points: HistoryTrendPoint[];
  page: number;
  total_days: number;
  total_pages: number;
}

export interface BatchError {
  index: number;
  file_name: string;
  code: string;
  message: string;
}

export interface BatchResponse {
  batch_id: string;
  total_images: number;
  processed_images: number;
  pending_images: number;
  succeeded_images: number;
  failed_images: number;
  completion_rate: number;
  results: PredictionResponse[];
  errors: BatchError[];
}
