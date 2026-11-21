"use client";

import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import { Maximize, Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/Primitives";
import { cn } from "@/lib/utils";

type Point = { x: number; y: number };
type ImageView = Point & { scale: number };

const fittedView = { scale: 1, x: 0, y: 0 };
const maxZoom = 4;
const zoomStep = 0.25;
const panKeys: Record<string, Point> = {
  ArrowLeft: { x: 32, y: 0 },
  ArrowRight: { x: -32, y: 0 },
  ArrowUp: { x: 0, y: 32 },
  ArrowDown: { x: 0, y: -32 },
};

function limit(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function midpoint(a: Point, b: Point) {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
}

export function ZoomablePredictionImage({ src, alt }: { src: string; alt: string }) {
  const frameRef = useRef<HTMLDivElement>(null);
  const pictureRef = useRef<HTMLImageElement>(null);
  const pointers = useRef(new Map<number, Point>());
  const [view, setView] = useState(fittedView);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const observer = new ResizeObserver(() => setView(fittedView));
    observer.observe(frame);
    return () => observer.disconnect();
  }, []);

  function changeView(scaleBy: (scale: number) => number, from = { x: 0, y: 0 }, to = from) {
    const frame = frameRef.current;
    const picture = pictureRef.current;
    if (!frame || !picture?.naturalWidth) return;

    const { clientWidth: width, clientHeight: height } = frame;
    const fit = Math.min(width / picture.naturalWidth, height / picture.naturalHeight);
    setView(current => {
      const scale = limit(scaleBy(current.scale), 1, maxZoom);
      if (scale === 1) return fittedView;
      const ratio = scale / current.scale;
      const maxX = Math.max(0, (picture.naturalWidth * fit * scale - width) / 2);
      const maxY = Math.max(0, (picture.naturalHeight * fit * scale - height) / 2);
      return {
        scale,
        x: limit(to.x - (from.x - current.x) * ratio, -maxX, maxX),
        y: limit(to.y - (from.y - current.y) * ratio, -maxY, maxY),
      };
    });
  }

  function startPointer(event: PointerEvent<HTMLDivElement>) {
    if (!ready || event.button !== 0 || (event.pointerType !== "touch" && view.scale === 1)) return;
    if (pointers.current.size >= 2) return;
    pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function movePointer(event: PointerEvent<HTMLDivElement>) {
    const previous = pointers.current.get(event.pointerId);
    if (!previous) return;
    const next = { x: event.clientX, y: event.clientY };
    pointers.current.set(event.pointerId, next);

    if (pointers.current.size === 1) {
      changeView(scale => scale, { x: 0, y: 0 }, { x: next.x - previous.x, y: next.y - previous.y });
      return;
    }

    const otherId = [...pointers.current.keys()].find(id => id !== event.pointerId);
    const other = otherId === undefined ? undefined : pointers.current.get(otherId);
    if (!other) return;
    const distance = Math.hypot(previous.x - other.x, previous.y - other.y);
    if (distance === 0) return;
    const ratio = Math.hypot(next.x - other.x, next.y - other.y) / distance;
    const bounds = event.currentTarget.getBoundingClientRect();
    const center = { x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2 };
    const before = midpoint(previous, other);
    const after = midpoint(next, other);
    changeView(scale => scale * ratio,
      { x: before.x - center.x, y: before.y - center.y },
      { x: after.x - center.x, y: after.y - center.y });
  }

  function endPointer(event: PointerEvent<HTMLDivElement>) {
    pointers.current.delete(event.pointerId);
  }

  function panWithKey(event: KeyboardEvent<HTMLDivElement>) {
    const direction = panKeys[event.key];
    if (view.scale === 1 || !direction) return;
    event.preventDefault();
    changeView(scale => scale, { x: 0, y: 0 }, direction);
  }

  return <>
    <div className={cn("prediction-zoom-frame", view.scale > 1 && "is-zoomed")} ref={frameRef}
      role="group" aria-label={view.scale > 1 ? "Dùng phím mũi tên để di chuyển ảnh" : "Khung xem ảnh"}
      tabIndex={view.scale > 1 ? 0 : undefined} onKeyDown={panWithKey}
      onPointerDown={startPointer} onPointerMove={movePointer} onPointerUp={endPointer}
      onPointerCancel={endPointer} onLostPointerCapture={endPointer}>
      {failed
        ? <div className="missing-picture"><span>Không có ảnh</span></div>
        : <img ref={pictureRef} src={src} alt={alt} draggable={false}
            onLoad={() => setReady(true)} onError={() => { setReady(false); setFailed(true); }}
            style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})` }} />}
    </div>
    <div className="prediction-zoom-controls" role="group" aria-label="Điều chỉnh kích thước ảnh">
      <Button variant="outline" aria-label="Thu nhỏ ảnh" disabled={!ready || view.scale <= 1}
        onClick={() => changeView(scale => scale - zoomStep)}><Minus aria-hidden /></Button>
      <output>{Math.round(view.scale * 100)}%</output>
      <Button variant="outline" aria-label="Phóng to ảnh" disabled={!ready || view.scale >= maxZoom}
        onClick={() => changeView(scale => scale + zoomStep)}><Plus aria-hidden /></Button>
      <Button variant="outline" disabled={!ready || view.scale === 1} onClick={() => setView(fittedView)}>
        <Maximize aria-hidden />Vừa khung
      </Button>
    </div>
  </>;
}
