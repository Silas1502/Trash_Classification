"use client";

import { useState } from "react";
import { ChevronDown, Download, List } from "lucide-react";
import type { BatchRow } from "@/components/classify/BatchImageUpload";
import { PredictionDetails } from "@/components/history/PredictionDetails";
import { Modal } from "@/components/ui/Modal";
import { Button, Empty, Notice, PanelTitle, PipelineBadge, SearchInput, Skeleton, WasteBadge } from "@/components/ui/Primitives";
import { Picture } from "@/components/ui/PredictionImages";
import { batchCsv } from "@/lib/batchCsv";
import { formatGateReading, gateLabels, predictionGates } from "@/lib/predictionGates";
import { downloadBlob, formatDuration } from "@/lib/utils";
import { wasteTypes, type WasteType } from "@/types";

export default function BatchResultTable({ rows, busy }: { rows: BatchRow[]; busy: boolean }) {
  const [search, setSearch] = useState("");
  const [waste, setWaste] = useState<WasteType | "">("");
  const [selected, setSelected] = useState<BatchRow>();
  const filtered = rows.filter(row => row.file.name.toLocaleLowerCase("vi").includes(search.trim().toLocaleLowerCase("vi")) &&
    (!waste || "error" in row || row.result.waste_type === waste));

  return <section className="panel batch-table-panel">
    <div className="panel-head batch-table-head">
      <PanelTitle icon={List}>Danh sách ảnh đã xử lý</PanelTitle>
      <div className="batch-filters">
        <SearchInput value={search} onChange={setSearch} placeholder="Tìm kiếm tên ảnh…" />
        <label className="input-wrap select-control">
          <select aria-label="Lọc loại rác" value={waste} onChange={event => setWaste(event.target.value as WasteType | "")}>
            <option value="">Loại rác: Tất cả</option>
            {wasteTypes.map(item => <option key={item} value={item}>Loại rác: {item}</option>)}
          </select><ChevronDown aria-hidden />
        </label>
      </div>
    </div>
    <div className="table-frame">
      <table className="data-table batch-table">
        <thead><tr>
          <th scope="col">Tên ảnh</th><th scope="col">Loại rác</th>
          <th scope="col">{gateLabels.confidence}</th><th scope="col">{gateLabels.margin}</th>
          <th scope="col">Luồng xử lý</th><th scope="col">Thời gian xử lý</th>
        </tr></thead>
        <tbody>{filtered.map(row => <tr key={row.id} onClick={() => setSelected(row)}>
          <td>
            <div className="file-cell">
              <Picture className="thumbnail" src={row.url} alt="" />
              <div>
                <button className="row-trigger" type="button" onClick={event => { event.stopPropagation(); setSelected(row); }} title={row.file.name}>{row.file.name}</button>
                {"error" in row && <div className="batch-file-error">
                  <span className="badge tone-red">{row.retryable ? "Chưa xử lý được" : "Không xử lý được"}</span>
                  <p>{row.error}</p>
                </div>}
              </div>
            </div>
          </td>
          {"result" in row ? <>
            <td><WasteBadge value={row.result.waste_type} /></td>
            {predictionGates(row.result).map(({ label, value, threshold }) => (
              <td key={label}>{formatGateReading(value, threshold)}</td>
            ))}
            <td><PipelineBadge value={row.result.pipeline_type} /></td>
            <td>{row.result.processing_time_ms == null ? "—" : formatDuration(row.result.processing_time_ms)}</td>
          </> : <><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td></>}
        </tr>)}</tbody>
      </table>
      {!filtered.length && (busy && !rows.length ? <Skeleton rows={3} /> : <Empty icon={List} title={rows.length ? "Không có ảnh khớp bộ lọc" : "Chưa có ảnh đã xử lý"}>
        {!rows.length && "Chọn ảnh hoặc thư mục rồi bắt đầu xử lý."}
      </Empty>)}
    </div>
    {rows.length > 0 && <div className="batch-export">
      <Button variant="outline" disabled={busy} onClick={() => {
        const csv = new Blob([batchCsv(rows)], { type: "text/csv;charset=utf-8" });
        downloadBlob(csv, "ket_qua_phan_loai_nhieu_anh.csv");
      }}><Download aria-hidden />Xuất CSV lượt xử lý</Button>
    </div>}
    <Notice>Nhấn vào một dòng để xem chi tiết kết quả.</Notice>
    {selected && <Modal title="Chi tiết dự đoán" onClose={() => setSelected(undefined)}>
      {"result" in selected ? <PredictionDetails result={selected.result} preview={selected.url} /> : <div className="failed-detail">
        <Picture src={selected.url} alt={selected.file.name} className="result-picture" /><strong>{selected.file.name}</strong><p>{selected.error}</p>
      </div>}
    </Modal>}
  </section>;
}
