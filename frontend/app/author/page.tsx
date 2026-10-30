"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { StatusBadge } from "@/components/Badges";
import { api, inr, when } from "@/lib/api";
import { useLiveRefresh } from "@/lib/live";
import type { Book, TicketSummary, User } from "@/lib/types";

export default function AuthorHome() {
  const [user, setUser] = useState<User | null>(null);
  const [books, setBooks] = useState<Book[]>([]);
  const [tickets, setTickets] = useState<TicketSummary[]>([]);

  const load = useCallback(() => {
    api<User>("/api/v1/auth/me").then(setUser).catch(() => undefined);
    api<Book[]>("/api/v1/books").then(setBooks).catch(() => undefined);
    api<TicketSummary[]>("/api/v1/tickets").then(setTickets).catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
  }, [load]);
  useLiveRefresh(load);

  const pending = books.reduce((sum, book) => sum + Number(book.royalty_pending || 0), 0);
  const openTickets = tickets.filter((ticket) => ticket.status === "open" || ticket.status === "in_progress");
  const inProduction = books.filter((book) => book.in_production);
  const first = user?.name.split(" ")[0];

  return (
    <div className="space-y-8">
      <div>
        <p className="font-note text-[11px] uppercase tracking-wider text-[#825c18]">Author desk folio</p>
        <h1 className="font-hand text-6xl leading-none text-[#2b2a27]">{first ? `Hello, ${first}` : "Hello"}</h1>
        <p className="font-serif mt-2 max-w-xl italic text-[#545148]">The standing of your titles and the queries still open with the desk.</p>
      </div>
      <section className="grid gap-4 md:grid-cols-3">
        <article className="sketch-card crayon-ochre p-5">
          <p className="font-note text-[11px] font-bold uppercase">Royalty pending</p>
          <p className="font-hand mt-2 text-5xl">{inr(pending)}</p>
          <p className="font-serif mt-2 text-sm">Paid quarterly, within 45 days of the quarter ending.</p>
        </article>
        <article className="sketch-card crayon-sage p-5">
          <p className="font-note text-[11px] font-bold uppercase">Open queries</p>
          <p className="font-hand mt-2 text-5xl">{openTickets.length}</p>
          <p className="font-serif mt-2 text-sm">Replies show up here without a refresh.</p>
        </article>
        <article className="sketch-card crayon-peach p-5">
          <p className="font-note text-[11px] font-bold uppercase">In production</p>
          <p className="font-hand mt-2 text-5xl">{inProduction.length}</p>
          <p className="font-serif mt-2 text-sm">{inProduction.length ? inProduction.map((book) => book.title).join(", ") : "Nothing waiting in the press."}</p>
        </article>
      </section>
      <section>
        <div className="mb-3 flex items-end justify-between">
          <h2 className="font-hand text-4xl">Recent queries</h2>
          <Link className="font-hand text-2xl underline decoration-wavy" href="/author/tickets/new">
            Raise a query
          </Link>
        </div>
        <div className="sketch-card overflow-hidden">
          {tickets.length === 0 ? (
            <p className="font-serif p-5 text-sm italic text-[#545148]">No queries yet.</p>
          ) : (
            <ul>
              {tickets.slice(0, 5).map((ticket) => (
                <li key={ticket.id} className="border-b border-dashed border-[#d6d0c2] last:border-0">
                  <Link className="grid gap-2 px-4 py-4 hover:bg-[#fffdf7] sm:grid-cols-[8rem_1fr_auto]" href={`/author/tickets/${ticket.id}`}>
                    <span className="font-note text-xs font-bold">{ticket.ticket_number}</span>
                    <span>
                      <span className="font-hand text-xl text-[#825c18]">{ticket.book_title || "General / account"}</span>
                      <span className="font-serif block text-sm">{ticket.subject}</span>
                    </span>
                    <span className="flex items-center gap-2 sm:justify-end">
                      <StatusBadge sketch status={ticket.status} />
                      <span className="font-note text-[11px] text-[#545148]">{when(ticket.updated_at)}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
