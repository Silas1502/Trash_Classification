"use client";

import { useId, useState } from "react";
import { ChartNoAxesColumnIncreasing, ChevronDown, ChevronUp } from "lucide-react";
import HistoryCharts from "@/components/history/HistoryCharts";
import { Button } from "@/components/ui/Primitives";

export default function HistoryAnalytics() {
  const id = useId();
  const [open, setOpen] = useState(false);

  return <section className="panel history-statistics" aria-labelledby={id}>
    <header className="analytics-header">
      <h2 id={id} className="analytics-heading"><ChartNoAxesColumnIncreasing aria-hidden />Thống kê</h2>
      <Button variant="icon" className="analytics-toggle" aria-label={open ? "Đóng thống kê" : "Mở thống kê"}
        aria-expanded={open} aria-controls={id + "-content"} onClick={() => setOpen(value => !value)}>
        {open ? <ChevronDown aria-hidden /> : <ChevronUp aria-hidden />}
      </Button>
    </header>
    <div id={id + "-content"} hidden={!open}><HistoryCharts active={open} /></div>
  </section>;
}
