"use client";

import { Portal } from "@/components/Portal";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <Portal role="admin">{children}</Portal>;
}
