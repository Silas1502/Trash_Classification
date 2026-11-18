export const wasteTypes = ["Nhựa", "Giấy", "Kim loại", "Thủy tinh", "Hữu cơ", "Khác"] as const;
export const pipelineTypes = ["Tự động", "Thủ công"] as const;
export type WasteType = typeof wasteTypes[number];
export type PipelineType = typeof pipelineTypes[number] | "Chưa thẩm định";

export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "error";
  model: "loaded" | "mock" | "error";
  database: "connected" | "disconnected" | "checking" | "not_configured";
  storage: "reachable" | "unreachable" | "checking" | "not_configured";
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
}

export interface HistoryItem extends PredictionResponse {
  metadata: {
    file_size: number;
    mime_type: string;
    inference_time_ms: number;
    xai_time_ms: number;
    processing_time_ms?: number | null;
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
