"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/services/api";

const labels = {
  checking: "Đang kết nối…",
  ready: "Hệ thống: Sẵn sàng",
  degraded: "Hệ thống: Hạn chế",
  offline: "Mất kết nối",
};

export default function SystemStatusBadge() {
  const [status, setStatus] = useState<keyof typeof labels>("checking");

  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    const controller = new AbortController();
    async function check() {
      try {
        const health = await getHealth(controller.signal);
        if (active) setStatus(health.status === "healthy" ? "ready" : health.status === "degraded" ? "degraded" : "offline");
      } catch {
        if (active) setStatus("offline");
      } finally {
        if (active) timer = window.setTimeout(check, 30000);
      }
    }
    void check();
    return () => { active = false; controller.abort(); window.clearTimeout(timer); };
  }, []);

  return <div className="system-status" role="status"><span className={"status-dot " + status} />{labels[status]}</div>;
}
