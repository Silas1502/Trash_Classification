"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { CircleAlert, CircleCheck, Info, X } from "lucide-react";

type Tone = "success" | "error" | "info";
const ToastContext = createContext<(message: string, tone?: Tone) => void>(() => {});
const icons = { success: CircleCheck, error: CircleAlert, info: Info };

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<{ id: number; message: string; tone: Tone }[]>([]);
  const nextId = useRef(0);
  const timers = useRef(new Map<number, number>());
  const dismiss = useCallback((id: number) => {
    window.clearTimeout(timers.current.get(id));
    timers.current.delete(id);
    setItems(items => items.filter(item => item.id !== id));
  }, []);
  const notify = useCallback((message: string, tone: Tone = "info") => {
    const id = ++nextId.current;
    setItems(items => [...items.slice(-3), { id, message, tone }]);
    timers.current.set(id, window.setTimeout(() => dismiss(id), 5500));
  }, [dismiss]);
  useEffect(() => {
    const active = timers.current;
    return () => { active.forEach(timer => window.clearTimeout(timer)); active.clear(); };
  }, []);
  return <ToastContext.Provider value={notify}>
    {children}
    <div className="toast-list" aria-live="polite">
      {items.map(({ id, message, tone }) => {
        const Icon = icons[tone];
        return <div className={"toast toast-" + tone} key={id}>
          <Icon aria-hidden /><span>{message}</span><button type="button" onClick={() => dismiss(id)} aria-label="Đóng thông báo"><X aria-hidden /></button>
        </div>;
      })}
    </div>
  </ToastContext.Provider>;
}

export function useToast() { return useContext(ToastContext); }
