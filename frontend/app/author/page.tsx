"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { StatusBadge } from "@/components/Badges";
import { api, inr } from "@/lib/api";
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

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">{user ? `Hello, ${user.name.split(" ")[0]}` : "Hello"}</h1>
        <p className="text-sm text-stone-600">Royalties, production, and open queries in one place.</p>
      </div>
      <section className="grid gap-4 sm:grid-cols-3">
        <article className="rounded-2xl border border-stone-200 bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-stone-500">Royalty pending</p>
          <p className="mt-2 text-2xl font-semibold">{inr(pending)}</p>
        </article>
        <article className="rounded-2xl border border-stone-200 bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-stone-500">Open queries</p>
          <p className="mt-2 text-2xl font-semibold">{openTickets.length}</p>
        </article>
        <article className="rounded-2xl border border-stone-200 bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-stone-500">In production</p>
          <p className="mt-2 text-2xl font-semibold">{inProduction.length}</p>
        </article>
      </section>
      {inProduction.length > 0 ? (
        <section>
          <h2 className="text-lg font-semibold">Still in production</h2>
          <ul className="mt-3 space-y-2">
            {inProduction.map((book) => (
              <li key={book.id} className="rounded-xl border border-stone-200 bg-white px-4 py-3 text-sm">
                <span className="font-medium">{book.title}</span>
                <span className="text-stone-500"> · {book.status}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <section>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent tickets</h2>
          <Link className="text-sm text-emerald-900 underline" href="/author/tickets/new">
            Raise a query
          </Link>
        </div>
        {tickets.length === 0 ? (
          <p className="mt-3 text-sm text-stone-500">No tickets yet.</p>
        ) : (
          <ul className="mt-3 divide-y divide-stone-200 overflow-hidden rounded-2xl border border-stone-200 bg-white">
            {tickets.slice(0, 5).map((ticket) => (
              <li key={ticket.id}>
                <Link className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-stone-50" href={`/author/tickets/${ticket.id}`}>
                  <span>
                    <span className="font-medium">{ticket.subject}</span>
                    <span className="block text-stone-500">{ticket.ticket_number}</span>
                  </span>
                  <StatusBadge status={ticket.status} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
