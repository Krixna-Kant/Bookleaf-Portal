"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { Book, TicketDetail } from "@/lib/types";

export default function NewTicketPage() {
  const router = useRouter();
  const [books, setBooks] = useState<Book[]>([]);
  const [bookId, setBookId] = useState("");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    api<Book[]>("/api/v1/books").then(setBooks).catch((err) => setError(err.message));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const ticket = await api<TicketDetail>("/api/v1/tickets", {
        method: "POST",
        body: JSON.stringify({
          book_id: bookId ? Number(bookId) : null,
          subject,
          description,
          attachment_names: files,
        }),
      });
      router.push(`/author/tickets/${ticket.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit the query");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold">Raise a query</h1>
      <p className="mt-1 text-sm text-stone-600">Tell us which book this is about, or choose a general account question.</p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-2xl border border-stone-200 bg-white p-5">
        <label className="block text-sm">
          Book
          <select className="mt-1" value={bookId} onChange={(event) => setBookId(event.target.value)}>
            <option value="">General / account level</option>
            {books.map((book) => (
              <option key={book.id} value={book.id}>
                {book.title} ({book.status})
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          Subject
          <input className="mt-1" value={subject} onChange={(event) => setSubject(event.target.value)} minLength={3} required />
        </label>
        <label className="block text-sm">
          Description
          <textarea className="mt-1 min-h-32" value={description} onChange={(event) => setDescription(event.target.value)} minLength={10} required />
        </label>
        <label className="block text-sm">
          Attachments
          <input
            className="mt-1"
            type="file"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files || []).map((file) => file.name))}
          />
          <span className="mt-1 block text-xs text-stone-500">
            File names are noted with the query. Upload storage is not enabled yet.
            {files.length ? ` Selected: ${files.join(", ")}` : ""}
          </span>
        </label>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button className="primary" disabled={pending} type="submit">
          {pending ? "Submitting…" : "Submit query"}
        </button>
      </form>
    </div>
  );
}
