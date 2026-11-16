import type { Metadata } from "next";
import type { ReactNode } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { ToastProvider } from "@/components/ui/Toast";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "Phân loại rác",
  description: "Phân loại rác từ hình ảnh và tra cứu kết quả dự đoán.",
  icons: { icon: "/recycling-logo.png" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <ToastProvider>
          <Sidebar />
          <main id="main" className="workspace">{children}</main>
        </ToastProvider>
      </body>
    </html>
  );
}
