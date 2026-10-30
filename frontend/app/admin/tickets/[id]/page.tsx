"use client";

import Link from "next/link";
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

  if (error && !ticket) return <p className="text-sm text-[#93000a]">{error}</p>;
  if (!ticket) return <p className="text-sm text-[#737970]">Opening the dossier…</p>;

  return (
    <div>
      <Link className="text-sm text-[#424840] hover:text-[#07290c]" href="/admin">
        ← Back to the queue
      </Link>
      <div className="mt-4 grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
        <section className="space-y-4">
          <article className="ops-card p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[#737970]">{ticket.ticket_number}</p>
            <h1 className="font-display mt-2 text-3xl text-[#07290c]">{ticket.subject}</h1>
            <p className="mt-2 text-sm text-[#424840]">
              {ticket.author_name} · {ticket.book_title || "General / account"} · opened {when(ticket.created_at)}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              <CategoryBadge category={ticket.category} />
              <span className="text-xs text-[#737970]">
                labels from {ticket.category_source}/{ticket.priority_source}
              </span>
            </div>
          </article>
          {ticket.book ? (
            <article className="grid gap-3 rounded-2xl bg-[#f0edea] p-5 sm:grid-cols-4">
              <Fact label="Status" value={ticket.book.status} />
              <Fact label="Copies sold" value={String(ticket.book.total_copies_sold)} />
              <Fact label="Royalty pending" value={inr(ticket.book.royalty_pending)} />
              <Fact label="Last payout" value={ticket.book.last_royalty_payout_date || "Never"} />
            </article>
          ) : null}
          <div className="space-y-3">
            {ticket.messages.map((message) => (
              <article key={message.id} className="rounded-2xl bg-[#f6f3ef] p-4">
                <p className="text-xs text-[#737970]">
                  {message.sender_name} · {message.sender_role} · {when(message.created_at)}
                </p>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{message.body}</p>
              </article>
            ))}
          </div>
          <form className="ops-card space-y-3 p-5" onSubmit={sendReply}>
            <div className="flex items-center justify-between">
              <h2 className="font-display text-xl text-[#07290c]">Reply</h2>
              <span className="rounded-full bg-[#ffdeaa] px-2 py-0.5 text-[11px] font-semibold text-[#271900]">Draft: {ticket.ai_draft_status}</span>
            </div>
            {ticket.ai_draft_status === "failed" ? (
              <p className="text-sm text-[#7d5700]">The model did not return a draft. Write the reply yourself.</p>
            ) : null}
            {ticket.ai_rationale ? <p className="text-xs text-[#737970]">Why this label: {ticket.ai_rationale}</p> : null}
            <textarea id="draft" className="ops-input min-h-40" value={draft} onChange={(event) => setDraft(event.target.value)} />
            <div className="flex flex-wrap gap-2">
              <button className="ops-btn" disabled={pending} type="submit">
                {pending ? "Sending…" : "Send to author"}
              </button>
              <button
                className="ops-btn-quiet"
                type="button"
                onClick={async () => {
                  await api(`/api/v1/admin/tickets/${params.id}/ai/regenerate-draft`, { method: "POST" });
                  load();
                }}
              >
                Regenerate draft
              </button>
            </div>
            {error ? <p className="text-sm text-[#93000a]">{error}</p> : null}
          </form>
        </section>
        <aside className="space-y-4">
          <section className="ops-card space-y-3 p-5">
            <h2 className="font-display text-xl text-[#07290c]">Manage</h2>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#737970]">
              Status
              <select className="ops-input mt-1" value={ticket.status} onChange={(event) => patch({ status: event.target.value })}>
                {Object.entries(STATUS_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#737970]">
              Category
              <select className="ops-input mt-1" value={ticket.category} onChange={(event) => patch({ category: event.target.value })}>
                {Object.entries(CATEGORY_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#737970]">
              Priority
              <select className="ops-input mt-1" value={ticket.priority} onChange={(event) => patch({ priority: event.target.value })}>
                {Object.entries(PRIORITY_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <p className="text-sm text-[#424840]">{ticket.assigned_to_name ? `Assigned to ${ticket.assigned_to_name}` : "Unassigned"}</p>
            <button
              className="ops-btn-quiet w-full"
              type="button"
              disabled={!me || ticket.assigned_to_id === me.id}
              onClick={async () => {
                const updated = await api<TicketDetail>(`/api/v1/admin/tickets/${params.id}/assign`, { method: "POST" });
                setTicket(updated);
              }}
            >
              {ticket.assigned_to_id === me?.id ? "Assigned to you" : "Assign to me"}
            </button>
          </section>
          <section className="rounded-2xl bg-[#f4efe0] p-5">
            <h2 className="font-display text-xl text-[#07290c]">Internal notes</h2>
            <p className="text-xs text-[#7d5700]">Visible to ops only.</p>
            <ul className="mt-3 space-y-2">
              {ticket.notes.map((item) => (
                <li key={item.id} className="rounded-lg bg-white px-3 py-2 text-sm">
                  <span className="block text-xs text-[#737970]">
                    {item.admin_name} · {when(item.created_at)}
                  </span>
                  {item.body}
                </li>
              ))}
            </ul>
            <form className="mt-3 space-y-2" onSubmit={addNote}>
              <textarea className="ops-input min-h-20" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Note for the team" />
              <button className="ops-btn-quiet" type="submit">
                Add note
              </button>
            </form>
          </section>
        </aside>
      </div>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wider text-[#737970]">{label}</p>
      <p className="mt-1 text-sm font-semibold text-[#1c1c1a]">{value}</p>
    </div>
  );
}
