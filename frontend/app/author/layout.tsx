"use client";

import { Portal } from "@/components/Portal";

export default function AuthorLayout({ children }: { children: React.ReactNode }) {
  return <Portal role="author">{children}</Portal>;
}
