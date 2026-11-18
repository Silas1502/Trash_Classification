"use client";

import { useEffect, useRef, useState } from "react";
import { ImageIcon, Images, Upload } from "lucide-react";
import BatchProgressBar from "@/components/classify/BatchProgressBar";
import BatchResultTable from "@/components/classify/BatchResultTable";
import { Button, PanelTitle } from "@/components/ui/Primitives";
import { useToast } from "@/components/ui/Toast";
import { readDroppedFiles } from "@/lib/dropFiles";
import { cn, imageAccept, isImage, maxImageBytes } from "@/lib/utils";
import { errorMessage } from "@/services/api";
import { groupUploads, predictBatch } from "@/services/predictService";
import type { PredictionResponse } from "@/types";

interface QueuedImage { id: number; file: File; url?: string }
type BatchErrorRow = QueuedImage & { error: string; retryable?: boolean };
export type BatchRow = (QueuedImage & { result: PredictionResponse }) | BatchErrorRow;

function validationError(file: File) {
  if (!isImage(file)) return "Định dạng không được hỗ trợ. Hãy dùng JPG, PNG hoặc WEBP.";
  if (file.size === 0) return "Tệp ảnh không có dữ liệu.";
  if (file.size > maxImageBytes) return "Ảnh vượt quá dung lượng tối đa 8 MB.";
}

export default function BatchImageUpload() {
  const [queue, setQueue] = useState<QueuedImage[]>([]);
  const [rows, setRows] = useState<BatchRow[]>([]);
  const [requestErrors, setRequestErrors] = useState<BatchErrorRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [reading, setReading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const filesInput = useRef<HTMLInputElement>(null);
  const sequence = useRef(0);
  const urls = useRef(new Set<string>());
  const request = useRef<AbortController | null>(null);
  const stopped = useRef(false);
  const mounted = useRef(true);
  const notify = useToast();

  useEffect(() => {
    mounted.current = true;
    const activeUrls = urls.current;
    return () => { mounted.current = false; request.current?.abort(); activeUrls.forEach(url => URL.revokeObjectURL(url)); activeUrls.clear(); };
  }, []);

  function clear() {
    if (request.current) return;
    urls.current.forEach(url => URL.revokeObjectURL(url));
    urls.current.clear();
    setQueue([]);
    setRows([]);
    setRequestErrors([]);
  }

  function select(files: File[]) {
    if (request.current || !mounted.current) return;
    clear();
    const rejected: BatchErrorRow[] = [];
    const items = files.map(file => {
      const item = { id: ++sequence.current, file };
      const error = validationError(file);
      if (error) {
        rejected.push({ ...item, error });
        return item;
      }
      const url = URL.createObjectURL(file);
      urls.current.add(url);
      return { ...item, url };
    });
    setQueue(items);
    setRows(rejected);
  }

  async function run() {
    if (request.current || reading || rows.length >= queue.length) return;
    const controller = new AbortController();
    request.current = controller;
    stopped.current = false;
    setBusy(true);
    setRequestErrors([]);
    let activeGroup: QueuedImage[] = [];
    try {
      const completed = new Set(rows.map(row => row.id));
      let failed = rows.filter(row => "error" in row).length;
      for (const group of groupUploads(queue.filter(item => !completed.has(item.id)))) {
        if (stopped.current || controller.signal.aborted) break;
        activeGroup = group;
        const response = await predictBatch(group.map(item => item.file), controller.signal);
        if (controller.signal.aborted) return;
        const errors = new Map(response.errors.map(error => [error.index, error.message]));
        let successIndex = 0;
        const next: BatchRow[] = group.map((item, index) => {
          const error = errors.get(index);
          if (error !== undefined) return { ...item, error };
          const result = response.results[successIndex++];
          return result ? { ...item, result } : { ...item, error: "Máy chủ không trả về kết quả cho ảnh này." };
        });
        failed += next.filter(row => "error" in row).length;
        setRows(previous => [...previous, ...next]);
        next.forEach(row => completed.add(row.id));
      }
      if (!controller.signal.aborted) {
        if (completed.size === queue.length) notify(failed ? "Đã kiểm tra xong. Có " + failed + " tệp không xử lý được." : "Đã xử lý xong tất cả ảnh.", failed ? "info" : "success");
        else if (stopped.current) notify("Đã dừng sau lô đang xử lý. Bạn có thể tiếp tục với các ảnh còn lại.");
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        const message = errorMessage(error, "Không thể xử lý lô ảnh lúc này.");
        setRequestErrors(activeGroup.map(item => ({ ...item, error: message, retryable: true })));
        notify(message + " Bạn có thể thử lại.", "error");
      }
    } finally {
      if (request.current === controller) { request.current = null; if (mounted.current) setBusy(false); }
    }
  }

  return <div className="flow">
    <div className="classify-grid">
      <section className="panel classify-card">
        <PanelTitle icon={Upload}>Tải ảnh hoặc thư mục</PanelTitle>
        <input type="file" ref={filesInput} className="sr-only" tabIndex={-1} aria-label="Nhiều tệp ảnh" accept={imageAccept} multiple disabled={busy || reading}
          onChange={event => { if (event.target.files?.length) select(Array.from(event.target.files)); event.target.value = ""; }} />
        <div className={cn("dropzone batch-dropzone", dragging && "dragging")}
          onDragOver={event => { event.preventDefault(); if (!busy && !reading) setDragging(true); }}
          onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); }}
          onDrop={async event => {
            event.preventDefault(); setDragging(false);
            if (busy || reading) return;
            setReading(true);
            try {
              const files = await readDroppedFiles(event.dataTransfer);
              if (files.length) select(files);
              else if (mounted.current) notify("Không tìm thấy tệp trong mục vừa thả.", "error");
            }
            catch { if (mounted.current) notify("Không đọc được thư mục. Hãy mở thư mục rồi chọn nhiều ảnh.", "error"); }
            finally { if (mounted.current) setReading(false); }
          }}>
          <Images className="drop-illustration" aria-hidden />
          <p>Kéo thả ảnh hoặc cả thư mục vào đây</p>
          <small>{reading ? "Đang đọc thư mục…" : queue.length ? "Đã chọn " + queue.length + " tệp." : "Hỗ trợ xử lý nhiều ảnh cùng lúc."}</small>
          <div className="drop-buttons">
            <Button disabled={busy || reading} onClick={() => filesInput.current?.click()}><ImageIcon aria-hidden />Chọn nhiều ảnh</Button>
          </div>
        </div>
      </section>
      <BatchProgressBar total={queue.length} processed={rows.length} failed={rows.filter(row => "error" in row).length}
        busy={busy} retryable={requestErrors.length > 0} hasProcessedUploads={rows.some(row => row.url !== undefined)}
        onStart={run} onStop={() => { if (!stopped.current) notify("Đang hoàn tất lô hiện tại trước khi dừng."); stopped.current = true; }} onReset={clear} />
    </div>
    <BatchResultTable key={queue[0]?.id ?? "empty"} rows={[...rows, ...requestErrors]} busy={busy} />
  </div>;
}
