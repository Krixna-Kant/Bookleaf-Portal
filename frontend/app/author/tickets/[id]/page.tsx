"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { CategoryBadge, PriorityBadge, StatusBadge } from "@/components/Badges";
import { api, when } from "@/lib/api";
import { useLiveRefresh } from "@/lib/live";
import type { TicketDetail } from "@/lib/types";

export default function AuthorTicketPage() {
  const params = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api<TicketDetail>(`/api/v1/tickets/${params.id}`)
      .then(setTicket)
      .catch((err) => setError(err.message));
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load]);
  useLiveRefresh(load);

  if (error) return <p className="font-serif text-sm text-[#9e3924]">{error}</p>;
  if (!ticket) return <p className="font-hand text-3xl">Finding the folio…</p>;

  return (
    <div className="mx-auto max-w-3xl">
      <Link className="font-hand text-2xl" href="/author/tickets">
        ← All tickets
      </Link>
      <article className="sketch-card mt-4 p-6">
        <p className="font-note text-xs font-bold">{ticket.ticket_number}</p>
        <h1 className="font-serif mt-2 text-3xl">{ticket.subject}</h1>
        <p className="font-hand mt-1 text-2xl text-[#825c18]">{ticket.book?.title || "General / account level"}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <StatusBadge sketch status={ticket.status} />
          <PriorityBadge sketch priority={ticket.priority} />
          <CategoryBadge sketch category={ticket.category} />
        </div>
      </article>
      <section className="mt-5 space-y-4">
        {ticket.messages.map((message) => (
          <article key={message.id} className={`rounded-lg border-2 border-[#2b2a27] p-5 ${message.sender_role === "admin" ? "border-l-8 border-l-[#2d5a27] bg-[#f6f3ea]" : "bg-[#fffdf8]"}`}>
            <p className="font-note text-[11px] uppercase tracking-wider text-[#545148]">
              {message.sender_name} · {message.sender_role} · {when(message.created_at)}
            </p>
            <p className="font-serif mt-3 whitespace-pre-wrap text-sm leading-6">{message.body}</p>
          </article>
        ))}
      </section>
      <p className="font-serif mt-6 text-sm italic text-[#545148]">This folio is read-only. The operations desk writes the replies.</p>
    </div>
  );
}
