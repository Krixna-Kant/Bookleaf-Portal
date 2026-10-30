"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { CategoryBadge, PriorityBadge, StatusBadge } from "@/components/Badges";
import { api, when } from "@/lib/api";
import { useLiveRefresh } from "@/lib/live";
import { CATEGORY_LABEL, PRIORITY_LABEL, STATUS_LABEL, type AdminStats, type TicketCategory, type TicketPriority, type TicketStatus, type TicketSummary } from "@/lib/types";

export default function AdminQueuePage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [tickets, setTickets] = useState<TicketSummary[] | null>(null);
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [q, setQ] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (category) params.set("category", category);
    if (priority) params.set("priority", priority);
    if (q.trim()) params.set("q", q.trim());
    api<AdminStats>("/api/v1/admin/stats").then(setStats).catch(() => undefined);
    api<TicketSummary[]>(`/api/v1/admin/tickets?${params.toString()}`).then(setTickets).catch(() => setTickets([]));
  }, [status, category, priority, q]);

  useEffect(() => {
    load();
  }, [load]);
  useLiveRefresh(load);

  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#737970]">Operations desk</p>
      <h1 className="font-display mt-1 text-4xl text-[#07290c]">Ticket queue</h1>
      <p className="mt-1 text-sm text-[#424840]">Urgent and oldest unresolved tickets stay at the top.</p>
      {stats ? (
        <div className="mt-5 flex flex-wrap gap-2 text-sm">
          <Chip label="Open" value={stats.open} />
          <Chip label="In progress" value={stats.in_progress} />
          <Chip label="Critical" value={stats.critical} tone="alert" />
          <Chip label="High" value={stats.high} tone="gold" />
          <Chip label="Aging 48h+" value={stats.aging_over_48h} />
        </div>
      ) : null}
      <div className="ops-card mt-5 grid gap-3 p-4 sm:grid-cols-4">
        <select className="ops-input" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select className="ops-input" value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">All categories</option>
          {Object.entries(CATEGORY_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select className="ops-input" value={priority} onChange={(event) => setPriority(event.target.value)}>
          <option value="">All priorities</option>
          {Object.entries(PRIORITY_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <input className="ops-input" placeholder="Search author, subject, or ticket" value={q} onChange={(event) => setQ(event.target.value)} />
      </div>
      {tickets === null ? (
        <p className="mt-6 text-sm text-[#737970]">Loading the queue…</p>
      ) : tickets.length === 0 ? (
        <p className="mt-6 text-sm text-[#737970]">No tickets match these filters.</p>
      ) : (
        <ul className="mt-5 overflow-hidden rounded-2xl bg-[#f6f3ef]">
          {tickets.map((ticket) => (
            <li key={ticket.id} className="border-b border-[#e5e2de] last:border-0">
              <Link className="block px-5 py-4 hover:bg-[#f0edea]" href={`/admin/tickets/${ticket.id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-[#07290c]">{ticket.ticket_number}</span>
                  <StatusBadge status={ticket.status as TicketStatus} />
                  <PriorityBadge priority={ticket.priority as TicketPriority} />
                  <CategoryBadge category={ticket.category as TicketCategory} />
                  {ticket.aging_hours > 48 && ticket.status !== "resolved" && ticket.status !== "closed" ? (
                    <span className="rounded-full bg-[#ffdeaa] px-2 py-0.5 text-[11px] font-semibold text-[#271900]">Aging {Math.round(ticket.aging_hours)}h</span>
                  ) : null}
                </div>
                <p className="mt-2 font-medium">{ticket.subject}</p>
                <p className="text-sm text-[#424840]">
                  {ticket.author_name} · {ticket.book_title || "General"} · {when(ticket.created_at)}
                  {ticket.assigned_to_name ? ` · ${ticket.assigned_to_name}` : " · Unassigned"}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Chip({ label, value, tone = "plain" }: { label: string; value: number; tone?: "plain" | "gold" | "alert" }) {
  const toneClass = tone === "alert" ? "bg-[#ffdad6] text-[#93000a]" : tone === "gold" ? "bg-[#ffdeaa] text-[#271900]" : "bg-[#f0edea] text-[#1c1c1a]";
  return (
    <span className={`rounded-full px-3 py-1 ${toneClass}`}>
      {label} <strong>{value}</strong>
    </span>
  );
}
