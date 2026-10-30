"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { CategoryBadge, PriorityBadge, StatusBadge } from "@/components/Badges";
import { api, when } from "@/lib/api";
import { useLiveRefresh } from "@/lib/live";
import type { TicketSummary } from "@/lib/types";

export default function TicketListPage() {
  const [tickets, setTickets] = useState<TicketSummary[] | null>(null);
  const load = useCallback(() => {
    api<TicketSummary[]>("/api/v1/tickets").then(setTickets).catch(() => setTickets([]));
  }, []);

  useEffect(() => {
    load();
  }, [load]);
  useLiveRefresh(load);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">My tickets</h1>
          <p className="text-sm text-stone-600">Replies appear here without a refresh.</p>
        </div>
        <Link className="primary inline-block" href="/author/tickets/new">
          New query
        </Link>
      </div>
      {tickets === null ? (
        <p className="mt-6 text-sm text-stone-500">Loading tickets…</p>
      ) : tickets.length === 0 ? (
        <p className="mt-6 text-sm text-stone-500">You have not raised a query yet.</p>
      ) : (
        <ul className="mt-6 divide-y divide-stone-200 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {tickets.map((ticket) => (
            <li key={ticket.id}>
              <Link className="block px-4 py-4 hover:bg-stone-50" href={`/author/tickets/${ticket.id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-stone-500">{ticket.ticket_number}</span>
                  <StatusBadge status={ticket.status} />
                  <PriorityBadge priority={ticket.priority} />
                  <CategoryBadge category={ticket.category} />
                </div>
                <p className="mt-2 font-medium">{ticket.subject}</p>
                <p className="text-sm text-stone-500">
                  {ticket.book_title || "General / account"} · {when(ticket.updated_at)}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
