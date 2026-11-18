"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChartNoAxesColumnIncreasing, Clock3, Layers } from "lucide-react";
import SystemStatusBadge from "@/components/layout/SystemStatusBadge";
import { cn } from "@/lib/utils";

const routes = [
  { href: "/classify", label: "Phân loại", icon: Layers },
  { href: "/history", label: "Lịch sử", icon: Clock3 },
  { href: "/statistics", label: "Thống kê", icon: ChartNoAxesColumnIncreasing },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      <Link className="branding" href="/classify">
        <Image className="brand-logo" src="/recycling-logo.png" width={36} height={36} alt="" unoptimized />
        <span>Phân loại rác</span>
      </Link>
      <nav aria-label="Điều hướng chính">
        {routes.map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}
            className={cn("nav-link", pathname === href && "current")}><Icon aria-hidden />{label}</Link>
        ))}
      </nav>
      <SystemStatusBadge />
    </aside>
  );
}
