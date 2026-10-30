"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { CategoryBadge, PriorityBadge, StatusBadge } from "@/components/Badges";
import { api, when } from "@/lib/api";
import { useLiveRefresh } from "@/lib/live";
import { CATEGORY_LABEL, PRIORITY_LABEL, STATUS_LABEL, type AdminStats, type TicketCategory, type TicketPriority, type TicketStatus, type TicketSummary } from "@/lib/types";

export default function AdminQueuePage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
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
    api<TicketSummary[]>(`/api/v1/admin/tickets?${params.toString()}`).then(setTickets).catch(() => undefined);
  }, [status, category, priority, q]);

  useEffect(() => {
    load();
  }, [load]);
  useLiveRefresh(load);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Ticket queue</h1>
      <p className="text-sm text-stone-600">Urgent and oldest unresolved tickets stay at the top.</p>
      {stats ? (
        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          <Chip label="Open" value={stats.open} />
          <Chip label="In progress" value={stats.in_progress} />
          <Chip label="Critical" value={stats.critical} />
          <Chip label="High" value={stats.high} />
          <Chip label="Aging 48h+" value={stats.aging_over_48h} />
        </div>
      ) : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">All categories</option>
          {Object.entries(CATEGORY_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select value={priority} onChange={(event) => setPriority(event.target.value)}>
          <option value="">All priorities</option>
          {Object.entries(PRIORITY_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <input placeholder="Search author, subject, or ticket" value={q} onChange={(event) => setQ(event.target.value)} />
      </div>
      <ul className="mt-6 divide-y divide-stone-200 overflow-hidden rounded-2xl border border-stone-200 bg-white">
        {tickets.map((ticket) => (
          <li key={ticket.id}>
            <Link className="block px-4 py-4 hover:bg-stone-50" href={`/admin/tickets/${ticket.id}`}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-stone-500">{ticket.ticket_number}</span>
                <StatusBadge status={ticket.status as TicketStatus} />
                <PriorityBadge priority={ticket.priority as TicketPriority} />
                <CategoryBadge category={ticket.category as TicketCategory} />
                {ticket.aging_hours > 48 && ticket.status !== "resolved" && ticket.status !== "closed" ? (
                  <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs text-red-800">Aging {Math.round(ticket.aging_hours)}h</span>
                ) : null}
              </div>
              <p className="mt-2 font-medium">{ticket.subject}</p>
              <p className="text-sm text-stone-500">
                {ticket.author_name} · {ticket.book_title || "General"} · {when(ticket.created_at)}
                {ticket.assigned_to_name ? ` · ${ticket.assigned_to_name}` : " · Unassigned"}
              </p>
            </Link>
          </li>
        ))}
      </ul>
      {tickets.length === 0 ? <p className="mt-4 text-sm text-stone-500">No tickets match these filters.</p> : null}
    </div>
  );
}

function Chip({ label, value }: { label: string; value: number }) {
  return (
    <span className="rounded-full bg-white px-3 py-1 ring-1 ring-stone-200">
      {label}: <strong>{value}</strong>
    </span>
  );
}
