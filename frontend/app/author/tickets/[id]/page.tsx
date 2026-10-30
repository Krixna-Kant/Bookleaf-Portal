"use client";

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

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!ticket) return <p className="text-sm text-stone-500">Loading ticket…</p>;

  return (
    <div className="max-w-3xl">
      <p className="text-xs text-stone-500">{ticket.ticket_number}</p>
      <h1 className="mt-1 text-2xl font-semibold">{ticket.subject}</h1>
      <div className="mt-3 flex flex-wrap gap-2">
        <StatusBadge status={ticket.status} />
        <PriorityBadge priority={ticket.priority} />
        <CategoryBadge category={ticket.category} />
      </div>
      <p className="mt-3 text-sm text-stone-600">{ticket.book?.title || "General / account level"}</p>
      <section className="mt-6 space-y-3">
        {ticket.messages.map((message) => (
          <article key={message.id} className="rounded-2xl border border-stone-200 bg-white p-4">
            <p className="text-xs text-stone-500">
              {message.sender_name} · {message.sender_role} · {when(message.created_at)}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm">{message.body}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
