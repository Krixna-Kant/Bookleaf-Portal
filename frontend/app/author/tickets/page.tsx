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
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-note text-[11px] uppercase tracking-wider text-[#825c18]">Correspondence</p>
          <h1 className="font-hand text-6xl leading-none">My tickets</h1>
        </div>
        <Link className="sketch-btn" href="/author/tickets/new">
          New query
        </Link>
      </div>
      {tickets === null ? (
        <p className="font-hand mt-6 text-2xl">Turning the pages…</p>
      ) : tickets.length === 0 ? (
        <p className="font-serif mt-6 italic text-[#545148]">You have not raised a query yet.</p>
      ) : (
        <ul className="sketch-card mt-6 overflow-hidden">
          {tickets.map((ticket) => (
            <li key={ticket.id} className="border-b border-dashed border-[#d6d0c2] last:border-0">
              <Link className="block px-4 py-4 hover:bg-[#fffdf7]" href={`/author/tickets/${ticket.id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-note text-xs font-bold">{ticket.ticket_number}</span>
                  <StatusBadge sketch status={ticket.status} />
                  <PriorityBadge sketch priority={ticket.priority} />
                  <CategoryBadge sketch category={ticket.category} />
                </div>
                <p className="font-serif mt-2">{ticket.subject}</p>
                <p className="font-note text-[11px] text-[#545148]">
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
