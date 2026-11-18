import type { BatchRow } from "@/components/classify/BatchImageUpload";

function csvCell(value: string | number | undefined) {
  if (typeof value !== "string") return value ?? "";
  const safe = /^[=+@-]/.test(value.trimStart()) || /^[\t\r\n]/.test(value) ? "'" + value : value;
  return '"' + safe.replaceAll('"', '""') + '"';
}

export function batchCsv(rows: BatchRow[]) {
  const headers = [
    "Tên tệp", "Loại rác", "Độ tin cậy (%)", "Ngưỡng độ tin cậy (%)", "Biên khoảng cách (điểm %)",
    "Ngưỡng biên (điểm %)", "Luồng xử lý", "Thời gian xử lý (ms)", "Trạng thái", "Lỗi",
  ];
  const records = [...rows].sort((a, b) => a.id - b.id).map(row => {
    const name = row.file.webkitRelativePath || row.file.name;
    if ("error" in row) {
      return [name, "", "", "", "", "", "", "", row.retryable ? "Chưa xử lý được" : "Không xử lý được", row.error];
    }
    const result = row.result;
    return [name, result.waste_type, result.confidence, result.checkpoint_1, result.margin, result.checkpoint_2,
      result.pipeline_type, result.processing_time_ms, result.status, ""];
  });
  return "\ufeff" + [headers, ...records].map(record => record.map(csvCell).join(",")).join("\r\n") + "\r\n";
}
