"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearSession } from "@/lib/api";
import type { Role, User } from "@/lib/types";

const AUTHOR_NAV = [
  { href: "/author", label: "Home" },
  { href: "/author/books", label: "My books" },
  { href: "/author/tickets", label: "My tickets" },
];

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
    return <p className={`p-10 ${role === "admin" ? "ops-shell font-sans-ops" : "paper-dots font-hand text-2xl"}`}>Opening the folio…</p>;
  }

  if (role === "admin") {
    return (
      <div className="ops-shell min-h-screen">
        <header className="sticky top-0 z-20 border-b border-[#e5e2de] bg-[#fcf9f5]">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-6">
            <div className="flex items-center gap-3">
              <span className="font-display text-xl text-[#07290c]">BookLeaf</span>
              <span className="rounded-full bg-[#ffdeaa] px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-[#271900]">Operations</span>
            </div>
            <nav className="flex items-center gap-6 text-sm">
              <Link className="border-b-2 border-[#1e3f20] pb-1 font-semibold text-[#07290c]" href="/admin">
                Queue
              </Link>
            </nav>
            <div className="text-right text-sm">
              <p className="font-semibold">{user.name}</p>
              <button className="text-xs text-[#737970] underline" onClick={() => { clearSession(); router.replace("/"); }} type="button">
                Sign out
              </button>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </div>
    );
  }

  return (
    <div className="paper-dots min-h-screen">
      <header className="sticky top-0 z-20 border-b-2 border-[#2b2a27] bg-[#faf6ee]/95">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-5 py-3">
          <div className="flex items-center gap-3">
            <span className="font-hand text-3xl leading-none text-[#2b2a27]">BookLeaf</span>
            <span className="hidden font-note text-[11px] uppercase tracking-wider text-[#545148] lg:inline">Author folio</span>
          </div>
          <nav className="flex items-center gap-4 font-hand text-lg">
            {AUTHOR_NAV.map((item) => {
              const active = pathname === item.href;
              return (
                <Link key={item.href} className={active ? "font-bold underline decoration-wavy decoration-[#825c18]" : "text-[#545148]"} href={item.href}>
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="flex items-center gap-3">
            <Link className="sketch-btn hidden sm:inline-flex" href="/author/tickets/new">
              New query
            </Link>
            <div className="text-right">
              <p className="font-hand text-xl leading-none">{user.name}</p>
              <button className="font-hand text-lg text-[#545148] underline decoration-wavy" onClick={() => { clearSession(); router.replace("/"); }} type="button">
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-5 py-8">{children}</main>
    </div>
  );
}
