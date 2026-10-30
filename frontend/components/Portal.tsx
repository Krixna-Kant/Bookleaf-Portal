"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearSession } from "@/lib/api";
import type { Role, User } from "@/lib/types";

const NAV: Record<Role, { href: string; label: string }[]> = {
  author: [
    { href: "/author", label: "Home" },
    { href: "/author/books", label: "My books" },
    { href: "/author/tickets", label: "My tickets" },
    { href: "/author/tickets/new", label: "New query" },
  ],
  admin: [{ href: "/admin", label: "Queue" }],
};

export function Portal({ role, children }: { role: Role; children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api<User>("/api/v1/auth/me")
      .then((me) => {
        if (me.role !== role) {
          router.replace(me.role === "admin" ? "/admin" : "/author");
          return;
        }
        setUser(me);
      })
      .catch(() => router.replace("/"));
  }, [role, router]);

  if (!user) {
    return <p className="p-10 text-sm text-stone-500">Loading your workspace…</p>;
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">BookLeaf</p>
            <p className="text-sm text-stone-500">{role === "admin" ? "Operations" : "Author support"}</p>
          </div>
          <nav className="flex flex-wrap items-center gap-2">
            {NAV[role].map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-full px-3 py-1.5 text-sm ${active ? "bg-emerald-900 text-white" : "text-stone-700 hover:bg-stone-100"}`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="text-right">
            <p className="text-sm font-medium">{user.name}</p>
            <button
              className="text-xs text-stone-500 underline"
              onClick={() => {
                clearSession();
                router.replace("/");
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
