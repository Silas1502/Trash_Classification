"use client";

import { useState } from "react";
import { ImageIcon, Images } from "lucide-react";
import SingleImageUpload from "@/components/classify/SingleImageUpload";
import BatchImageUpload from "@/components/classify/BatchImageUpload";

export default function ClassifyPage() {
  const [mode, setMode] = useState<"single" | "batch">("single");

  return <div className="page classify-page">
    <h1>Phân loại rác thải sinh hoạt</h1>
    <div className="classify-tabs" role="group" aria-label="Chế độ phân loại">
      <button type="button" aria-pressed={mode === "single"} onClick={() => setMode("single")}><ImageIcon aria-hidden />Một ảnh</button>
      <button type="button" aria-pressed={mode === "batch"} onClick={() => setMode("batch")}><Images aria-hidden />Nhiều ảnh</button>
    </div>
    <div hidden={mode !== "single"}><SingleImageUpload /></div>
    <div hidden={mode !== "batch"}><BatchImageUpload /></div>
  </div>;
}
