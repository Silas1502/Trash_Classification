import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { CircleAlert, CircleCheck, Clock3, ImageIcon, Info, Recycle, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PipelineType, PredictionResponse, WasteType } from "@/types";

export function Button({ className, variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "outline" | "icon" }) {
  return <button type="button" className={cn("button", "button-" + variant, className)} {...props} />;
}

export function PanelTitle({ icon: Icon, children, className }: { icon: LucideIcon; children: ReactNode; className?: string }) {
  return <h2 className={cn("panel-title", className)}><Icon aria-hidden />{children}</h2>;
}

export function Notice({ children }: { children: ReactNode }) {
  return <div className="notice"><Info aria-hidden /><div>{children}</div></div>;
}

export function Empty({ icon: Icon = ImageIcon, title, children }: { icon?: LucideIcon; title: string; children?: ReactNode }) {
  return <div className="empty"><Icon aria-hidden /><strong>{title}</strong>{children && <p>{children}</p>}</div>;
}

export function ProgressBar({ value, label }: { value: number; label: string }) {
  return <div className="progress-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}>
    <div className="progress-fill" style={{ width: Math.min(100, Math.max(0, value)) + "%" }} />
  </div>;
}

const wasteColors: Record<WasteType, string> = { "Nhựa": "blue", "Giấy": "gold", "Kim loại": "slate", "Thủy tinh": "green", "Hữu cơ": "sand", "Khác": "violet" };
export function WasteBadge({ value }: { value: WasteType }) {
  return <span className={"badge waste-badge tone-" + wasteColors[value]}><Recycle aria-hidden />{value}</span>;
}

export function PipelineBadge({ value }: { value: PipelineType }) {
  if (value === "Chưa thẩm định") return <span className="badge tone-slate">{value}</span>;
  return value === "Tự động" ? <span className="badge tone-green"><CircleCheck aria-hidden />Tự động</span>
    : <span className="badge tone-amber"><Clock3 aria-hidden />Thủ công</span>;
}

export function StatusBadge({ value }: { value: PredictionResponse["status"] }) {
  if (value === "Chưa thẩm định") return <span className="badge tone-slate">{value}</span>;
  return value === "Thành công" ? <span className="badge tone-green"><CircleCheck aria-hidden />Kết quả hợp lệ</span>
    : <span className="badge tone-amber"><CircleAlert aria-hidden />Cần kiểm tra</span>;
}

export function SearchInput({ value, onChange, placeholder = "Tìm kiếm tên file…" }: { value: string; onChange: (value: string) => void; placeholder?: string }) {
  return <label className="input-wrap search-control"><Search aria-hidden /><input aria-label={placeholder} placeholder={placeholder} value={value} maxLength={150}
    type="search" onChange={event => onChange(event.target.value)} /></label>;
}

export function Skeleton({ rows = 4 }: { rows?: number }) {
  return <div className="skeleton-stack" role="status" aria-label="Đang tải">
    {Array.from({ length: rows }, (_, i) => <div className="skeleton" key={i} />)}
  </div>;
}
