import type { Metadata } from "next";
import HistoryCharts from "@/components/history/HistoryCharts";

export const metadata: Metadata = {
  title: "Thống kê | Phân loại rác",
};

export default function StatisticsPage() {
  return <div className="page">
    <header className="page-header"><h1 id="statistics-heading">Thống kê</h1></header>
    <section className="panel" aria-labelledby="statistics-heading"><HistoryCharts /></section>
  </div>;
}
