"use client";

import { useEffect, useRef, useState } from "react";
import { FolderOpen, ImageIcon, LoaderCircle, Play, RefreshCw, Upload } from "lucide-react";
import SingleImageResult, { SingleImageXai } from "@/components/classify/SingleImageResult";
import { Button, Empty, Notice, PanelTitle } from "@/components/ui/Primitives";
import { Picture } from "@/components/ui/PredictionImages";
import { useToast } from "@/components/ui/Toast";
import { cn, formatSize, imageAccept, isImage } from "@/lib/utils";
import { errorMessage } from "@/services/api";
import { predictSingle } from "@/services/predictService";
import type { PredictionResponse } from "@/types";

export default function SingleImageUpload() {
  const [selection, setSelection] = useState<{ file: File; url: string }>();
  const [result, setResult] = useState<PredictionResponse>();
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const request = useRef<AbortController | null>(null);
  const notify = useToast();
  const preview = selection?.url;

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  useEffect(() => () => request.current?.abort(), []);

  function select(files: File[]) {
    if (request.current) return;
    if (files.length !== 1 || !isImage(files[0])) {
      notify("Vui lòng chọn đúng một ảnh JPG, PNG hoặc WEBP.", "error");
      return;
    }
    if (files[0].size === 0 || files[0].size > 8 * 1024 ** 2) {
      notify("Ảnh phải có dữ liệu và không vượt quá 8 MB.", "error");
      return;
    }
    setSelection({ file: files[0], url: URL.createObjectURL(files[0]) });
    setResult(undefined);
  }

  async function run() {
    if (!selection || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setResult(undefined);
    try {
      const data = await predictSingle(selection.file, controller.signal);
      if (!controller.signal.aborted) {
        setResult(data);
        notify("Đã phân loại ảnh.", "success");
      }
    } catch (error) {
      if (!controller.signal.aborted) notify(errorMessage(error, "Không thể phân loại ảnh. Vui lòng thử lại."), "error");
    } finally {
      if (request.current === controller) { request.current = null; setBusy(false); }
    }
  }

  return <div className="flow">
    <div className="classify-grid">
      <section className="panel classify-card">
        <PanelTitle icon={Upload}>Tải hình ảnh lên</PanelTitle>
        <input ref={input} type="file" className="sr-only" tabIndex={-1} aria-label="Tệp ảnh" accept={imageAccept} disabled={busy}
          onChange={event => { if (event.target.files?.length) select(Array.from(event.target.files)); event.target.value = ""; }} />
        <div className={cn("dropzone", dragging && "dragging")}
          onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }}
          onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); }}
          onDrop={event => { event.preventDefault(); setDragging(false); select(Array.from(event.dataTransfer.files)); }}>
          <ImageIcon className="drop-illustration" aria-hidden />
          <p>Kéo thả ảnh vào đây hoặc <button className="text-link" type="button" disabled={busy} onClick={() => input.current?.click()}>chọn tệp</button></p>
          {!selection && <small>JPG, PNG, WEBP · Tối đa 8 MB</small>}
          <Button disabled={busy} onClick={() => input.current?.click()}><FolderOpen aria-hidden />Chọn ảnh</Button>
        </div>
        {selection ? <div className="upload-preview">
          <Picture className="preview-picture" src={preview} alt={"Ảnh xem trước: " + selection.file.name} />
          <div className="preview-caption"><ImageIcon aria-hidden /><span title={selection.file.name}>{selection.file.name}</span><small>{formatSize(selection.file.size)}</small></div>
        </div> : <div className="upload-preview empty-preview">
          <Empty title="Chưa chọn ảnh">Ảnh đã chọn sẽ xuất hiện ở đây.</Empty>
        </div>}
        <div className="single-actions">
          <Button disabled={!selection || busy} onClick={run}>{busy ? <LoaderCircle className="spin" aria-hidden /> : <Play className="play-icon" aria-hidden />}{busy ? "Đang dự đoán…" : "Bắt đầu dự đoán"}</Button>
          <Button variant="outline" disabled={busy || !selection} onClick={() => { setSelection(undefined); setResult(undefined); }}><RefreshCw aria-hidden />Làm mới</Button>
        </div>
      </section>
      <SingleImageResult result={result} busy={busy} />
    </div>
    {result && <SingleImageXai key={result.id} result={result} preview={preview} />}
    <Notice>Hỗ trợ dự đoán cho 1 ảnh mỗi lần.</Notice>
  </div>;
}
