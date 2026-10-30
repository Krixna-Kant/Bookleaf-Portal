"use client";

import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { CategoryBadge, PriorityBadge, StatusBadge } from "@/components/Badges";
import { ApiError, api, inr, when } from "@/lib/api";
import { useLiveRefresh } from "@/lib/live";
import { CATEGORY_LABEL, PRIORITY_LABEL, STATUS_LABEL, type TicketDetail, type User } from "@/lib/types";

export default function AdminTicketPage() {
  const params = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [me, setMe] = useState<User | null>(null);
  const [draft, setDraft] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const load = useCallback(() => {
    api<TicketDetail>(`/api/v1/admin/tickets/${params.id}`)
      .then((next) => {
        setTicket(next);
        setDraft((current) => (current && document.activeElement?.id === "draft" ? current : next.ai_draft || ""));
      })
      .catch((err) => setError(err.message));
  }, [params.id]);

  useEffect(() => {
    api<User>("/api/v1/auth/me").then(setMe).catch(() => undefined);
    load();
  }, [load]);
  useLiveRefresh(load);

  async function patch(body: Record<string, string | number>) {
    setError("");
    const updated = await api<TicketDetail>(`/api/v1/admin/tickets/${params.id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    setTicket(updated);
  }

  async function sendReply(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim()) return;
    setPending(true);
    setError("");
    try {
      const updated = await api<TicketDetail>(`/api/v1/admin/tickets/${params.id}/replies`, {
        method: "POST",
        body: JSON.stringify({ body: draft }),
      });
      setTicket(updated);
      setDraft("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send the reply");
    } finally {
      setPending(false);
    }
  }

  async function addNote(event: FormEvent) {
    event.preventDefault();
    if (!note.trim()) return;
    const updated = await api<TicketDetail>(`/api/v1/admin/tickets/${params.id}/notes`, {
      method: "POST",
      body: JSON.stringify({ body: note }),
    });
    setTicket(updated);
    setNote("");
  }

  if (error && !ticket) return <p className="text-sm text-red-700">{error}</p>;
  if (!ticket) return <p className="text-sm text-stone-500">Loading ticket…</p>;

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
      <section>
        <p className="text-xs text-stone-500">{ticket.ticket_number}</p>
        <h1 className="mt-1 text-2xl font-semibold">{ticket.subject}</h1>
        <p className="mt-2 text-sm text-stone-600">
          {ticket.author_name} · {ticket.book_title || "General / account"} · opened {when(ticket.created_at)}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <StatusBadge status={ticket.status} />
          <PriorityBadge priority={ticket.priority} />
          <CategoryBadge category={ticket.category} />
          <span className="text-xs text-stone-500">
            labels from {ticket.category_source}/{ticket.priority_source}
          </span>
        </div>
        {ticket.book ? (
          <p className="mt-3 text-sm text-stone-700">
            {ticket.book.status} · sold {ticket.book.total_copies_sold} · pending {inr(ticket.book.royalty_pending)} · last payout{" "}
            {ticket.book.last_royalty_payout_date || "never"}
          </p>
        ) : null}
        <div className="mt-5 space-y-3">
          {ticket.messages.map((message) => (
            <article key={message.id} className="rounded-2xl border border-stone-200 bg-white p-4">
              <p className="text-xs text-stone-500">
                {message.sender_name} · {message.sender_role} · {when(message.created_at)}
              </p>
              <p className="mt-2 whitespace-pre-wrap text-sm">{message.body}</p>
            </article>
          ))}
        </div>
        <form onSubmit={sendReply} className="mt-5 space-y-3 rounded-2xl border border-stone-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <h2 className="font-medium">Reply</h2>
            <span className="text-xs text-stone-500">Draft: {ticket.ai_draft_status}</span>
          </div>
          {ticket.ai_draft_status === "failed" ? (
            <p className="text-sm text-amber-800">The model did not return a draft. Write the reply yourself.</p>
          ) : null}
          {ticket.ai_rationale ? <p className="text-xs text-stone-500">Why this label: {ticket.ai_rationale}</p> : null}
          <textarea id="draft" className="min-h-40" value={draft} onChange={(event) => setDraft(event.target.value)} />
          <div className="flex gap-2">
            <button className="primary" disabled={pending} type="submit">
              {pending ? "Sending…" : "Send to author"}
            </button>
            <button
              className="secondary"
              type="button"
              onClick={async () => {
                await api(`/api/v1/admin/tickets/${params.id}/ai/regenerate-draft`, { method: "POST" });
                load();
              }}
            >
              Regenerate draft
            </button>
          </div>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
        </form>
      </section>
      <aside className="space-y-4">
        <section className="rounded-2xl border border-stone-200 bg-white p-4 space-y-3">
          <h2 className="font-medium">Manage</h2>
          <label className="block text-sm">
            Status
            <select className="mt-1" value={ticket.status} onChange={(event) => patch({ status: event.target.value })}>
              {Object.entries(STATUS_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            Category
            <select className="mt-1" value={ticket.category} onChange={(event) => patch({ category: event.target.value })}>
              {Object.entries(CATEGORY_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            Priority
            <select className="mt-1" value={ticket.priority} onChange={(event) => patch({ priority: event.target.value })}>
              {Object.entries(PRIORITY_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="secondary w-full"
            type="button"
            disabled={!me}
            onClick={async () => {
              if (!me) return;
              const updated = await api<TicketDetail>(`/api/v1/admin/tickets/${params.id}/assign`, { method: "POST" });
              setTicket(updated);
            }}
          >
            {ticket.assigned_to_id === me?.id ? "Assigned to you" : "Assign to me"}
          </button>
        </section>
        <section className="rounded-2xl border border-stone-200 bg-white p-4">
          <h2 className="font-medium">Internal notes</h2>
          <p className="text-xs text-stone-500">Visible to ops only.</p>
          <ul className="mt-3 space-y-2">
            {ticket.notes.map((item) => (
              <li key={item.id} className="rounded-lg bg-amber-50 px-3 py-2 text-sm">
                <span className="block text-xs text-stone-500">
                  {item.admin_name} · {when(item.created_at)}
                </span>
                {item.body}
              </li>
            ))}
          </ul>
          <form onSubmit={addNote} className="mt-3 space-y-2">
            <textarea className="min-h-20" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Note for the team" />
            <button className="secondary" type="submit">
              Add note
            </button>
          </form>
        </section>
      </aside>
    </div>
  );
}
