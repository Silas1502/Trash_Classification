"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/Primitives";
import { cn } from "@/lib/utils";

export function Modal({ title, onClose, children, wide = false }: { title: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => { dialog?.close(); };
  }, []);

  function close() {
    ref.current?.close();
    onClose();
  }

  return <dialog className={cn("modal panel", wide && "modal-wide")} ref={ref} aria-labelledby={id}
    onCancel={event => { event.preventDefault(); close(); }}
    onClick={event => { if (event.target === event.currentTarget) close(); }}>
    <div className="modal-content">
      <div className="panel-head"><h2 id={id} className="panel-title">{title}</h2><Button variant="icon" onClick={close} aria-label="Đóng chi tiết"><X aria-hidden /></Button></div>
      {children}
    </div>
  </dialog>;
}
