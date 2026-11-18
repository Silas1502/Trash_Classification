"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, FolderOpen, ImageIcon, Images, LoaderCircle, Play, RefreshCw, Upload } from "lucide-react";
import SingleImageResult, { SingleImageXai } from "@/components/classify/SingleImageResult";
import { Modal } from "@/components/ui/Modal";
import { Button, Empty, Notice, PanelTitle } from "@/components/ui/Primitives";
import { Picture } from "@/components/ui/PredictionImages";
import { useToast } from "@/components/ui/Toast";
import { prepareCameraImage } from "@/lib/cameraImage";
import { cn, formatSize, imageAccept, isImage, maxImageBytes } from "@/lib/utils";
import { errorMessage } from "@/services/api";
import { predictSingle } from "@/services/predictService";
import type { PredictionResponse } from "@/types";

const samples = [
  { file: "nhua.jpg", label: "Nhựa" },
  { file: "giay.jpg", label: "Giấy" },
  { file: "kim-loai.jpg", label: "Kim loại" },
  { file: "thuy-tinh.jpg", label: "Thủy tinh" },
  { file: "can-kiem-tra.jpg", label: "Tình huống cần kiểm tra" },
];

export default function SingleImageUpload() {
  const [selection, setSelection] = useState<{ file: File; url: string }>();
  const [result, setResult] = useState<PredictionResponse>();
  const [busy, setBusy] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [samplesOpen, setSamplesOpen] = useState(false);
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const camera = useRef<HTMLInputElement>(null);
  const request = useRef<AbortController | null>(null);
  const sourceRequest = useRef<AbortController | null>(null);
  const notify = useToast();
  const preview = selection?.url;
  const locked = busy || preparing;

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  useEffect(() => () => { request.current?.abort(); sourceRequest.current?.abort(); }, []);

  function select(files: File[]) {
    if (request.current) return;
    if (files.length !== 1 || !isImage(files[0])) {
      notify("Vui lòng chọn đúng một ảnh JPG, PNG hoặc WEBP.", "error");
      return;
    }
    if (files[0].size === 0 || files[0].size > maxImageBytes) {
      notify("Ảnh phải có dữ liệu và không vượt quá 8 MB.", "error");
      return;
    }
    setSelection({ file: files[0], url: URL.createObjectURL(files[0]) });
    setResult(undefined);
  }

  async function prepareSelection(load: (signal: AbortSignal) => Promise<File>, failure: string) {
    if (request.current || sourceRequest.current) return;
    const controller = new AbortController();
    sourceRequest.current = controller;
    setPreparing(true);
    try {
      const file = await load(controller.signal);
      if (!controller.signal.aborted) select([file]);
    } catch {
      if (!controller.signal.aborted) notify(failure, "error");
    } finally {
      sourceRequest.current = null;
      if (!controller.signal.aborted) setPreparing(false);
    }
  }

  function selectSample(fileName: string) {
    setSamplesOpen(false);
    void prepareSelection(async signal => {
      const response = await fetch("/demo/" + fileName, { signal });
      if (!response.ok) throw new Error("Không tải được ảnh mẫu.");
      return new File([await response.blob()], "mau-" + fileName, { type: "image/jpeg" });
    }, "Không tải được ảnh mẫu. Vui lòng thử lại.");
  }

  async function run() {
    if (!selection || request.current || sourceRequest.current) return;
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
        <input ref={input} type="file" className="sr-only" tabIndex={-1} aria-label="Tệp ảnh" accept={imageAccept} disabled={locked}
          onChange={event => { if (event.target.files?.length) select(Array.from(event.target.files)); event.target.value = ""; }} />
        <input ref={camera} type="file" className="sr-only" tabIndex={-1} aria-label="Ảnh camera" accept="image/*" capture="environment" disabled={locked}
          onChange={event => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) void prepareSelection(() => prepareCameraImage(file), "Không đọc được ảnh camera. Hãy thử chụp ở định dạng JPG hoặc chọn ảnh đã lưu.");
          }} />
        <div className={cn("dropzone", dragging && "dragging")}
          onDragOver={event => { event.preventDefault(); if (!locked) setDragging(true); }}
          onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); }}
          onDrop={event => {
            event.preventDefault();
            setDragging(false);
            if (!locked) select(Array.from(event.dataTransfer.files));
          }}>
          <ImageIcon className="drop-illustration" aria-hidden />
          <p>Kéo thả ảnh vào đây hoặc <button className="text-link" type="button" disabled={locked} onClick={() => input.current?.click()}>chọn tệp</button></p>
          {preparing ? <small role="status">Đang chuẩn bị ảnh…</small> : !selection && <small>JPG, PNG, WEBP · Tối đa 8 MB</small>}
          <div className="drop-buttons">
            <Button disabled={locked} onClick={() => input.current?.click()}><FolderOpen aria-hidden />Chọn ảnh</Button>
            <Button variant="outline" className="camera-button" disabled={locked} onClick={() => camera.current?.click()}><Camera aria-hidden />Chụp ảnh</Button>
            <Button variant="outline" disabled={locked} onClick={() => setSamplesOpen(true)}><Images aria-hidden />Chọn ảnh mẫu</Button>
          </div>
        </div>
        {selection ? <div className="upload-preview">
          <Picture className="preview-picture" src={preview} alt={"Ảnh xem trước: " + selection.file.name} />
          <div className="preview-caption"><ImageIcon aria-hidden /><span title={selection.file.name}>{selection.file.name}</span><small>{formatSize(selection.file.size)}</small></div>
        </div> : <div className="upload-preview empty-preview">
          <Empty title="Chưa chọn ảnh">Ảnh đã chọn sẽ xuất hiện ở đây.</Empty>
        </div>}
        <div className="single-actions">
          <Button disabled={!selection || locked} onClick={run}>{busy ? <LoaderCircle className="spin" aria-hidden /> : <Play className="play-icon" aria-hidden />}{busy ? "Đang dự đoán…" : "Bắt đầu dự đoán"}</Button>
          <Button variant="outline" disabled={locked || !selection} onClick={() => { setSelection(undefined); setResult(undefined); }}><RefreshCw aria-hidden />Làm mới</Button>
        </div>
      </section>
      <SingleImageResult result={result} busy={busy} />
    </div>
    {result && <SingleImageXai key={result.id} result={result} preview={preview} />}
    {samplesOpen && <Modal title="Chọn ảnh mẫu" onClose={() => setSamplesOpen(false)}>
      <div className="sample-picker">
        {samples.map(({ file, label }) => <Button className="sample-option" key={file} variant="outline" onClick={() => selectSample(file)}>
          <Picture className="sample-picture" src={"/demo/" + file} alt="" />
          {label}
        </Button>)}
      </div>
    </Modal>}
    <Notice>Hỗ trợ dự đoán cho 1 ảnh mỗi lần.</Notice>
  </div>;
}
