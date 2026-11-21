"use client";

import { useState } from "react";
import { ImageIcon } from "lucide-react";
import { ZoomablePredictionImage } from "@/components/ui/ZoomablePredictionImage";
import { cn } from "@/lib/utils";

export function Picture({ src, alt, className }: { src?: string | null; alt: string; className?: string }) {
  const [failedSrc, setFailedSrc] = useState<string>();
  if (!src || failedSrc === src) return <div className={cn("missing-picture", className)}><ImageIcon aria-hidden /><span>Không có ảnh</span></div>;
  return <img className={className} src={src} alt={alt} onError={() => setFailedSrc(src)} />;
}

export function PredictionImages({ original, heatmap, energy, comparison = false, zoomable = false }: {
  original?: string | null;
  heatmap?: string | null;
  energy?: string | null;
  comparison?: boolean;
  zoomable?: boolean;
}) {
  const [view, setView] = useState<"original" | "heatmap" | "energy">("original");
  const images = {
    original: { label: "Ảnh gốc", src: original, alt: "Ảnh gốc dùng để phân loại" },
    heatmap: { label: "Bản đồ nhiệt Grad-CAM", src: heatmap, alt: "Ảnh phủ nhiệt Grad-CAM" },
    energy: { label: "Spatial Energy", src: energy, alt: "Ảnh phủ Spatial Energy" },
  };
  const views = ["original", "heatmap", "energy"] as const;

  if (comparison) {
    return <div className="images comparison">
      {views.map(name => {
        const { label, src, alt } = images[name];
        return <figure key={name}>
          <figcaption><ImageIcon aria-hidden />{label}</figcaption>
          <Picture className="result-picture" src={src} alt={alt} />
        </figure>;
      })}
    </div>;
  }

  const { src, alt } = images[view];
  return <>
    <div className="image-tabs" role="group" aria-label="Chế độ xem ảnh">
      {views.map(name => (
        <button type="button" key={name} aria-pressed={view === name} onClick={() => setView(name)}>
          {images[name].label}
        </button>
      ))}
    </div>
    {zoomable && src
      ? <ZoomablePredictionImage key={`${view}:${src}`} src={src} alt={alt} />
      : <Picture className={cn("result-picture", zoomable && "prediction-zoom-frame")} src={src} alt={alt} />}
  </>;
}
