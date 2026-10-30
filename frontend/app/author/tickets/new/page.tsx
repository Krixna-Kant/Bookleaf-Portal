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
    <div className="mx-auto max-w-2xl">
      <p className="font-note text-[11px] uppercase tracking-wider text-[#825c18]">Author support docket</p>
      <h1 className="font-hand text-6xl leading-none">Raise a query</h1>
      <p className="font-serif mt-2 italic text-[#545148]">Tell the desk which book this is about, or leave it as a general account question.</p>
      <form className="sketch-card mt-6 space-y-4 p-6" onSubmit={onSubmit}>
        <label className="block font-note text-[11px] font-bold uppercase">
          Book
          <select className="sketch-input mt-1" value={bookId} onChange={(event) => setBookId(event.target.value)}>
            <option value="">General / account level</option>
            {books.map((book) => (
              <option key={book.id} value={book.id}>
                {book.title} ({book.status})
              </option>
            ))}
          </select>
        </label>
        <label className="block font-note text-[11px] font-bold uppercase">
          Subject
          <input className="sketch-input mt-1" value={subject} minLength={3} onChange={(event) => setSubject(event.target.value)} required />
        </label>
        <label className="block font-note text-[11px] font-bold uppercase">
          Description
          <textarea className="sketch-input mt-1 min-h-36" value={description} minLength={10} onChange={(event) => setDescription(event.target.value)} required />
        </label>
        <label className="block font-note text-[11px] font-bold uppercase">
          Attachments
          <input className="sketch-input mt-1" type="file" multiple onChange={(event) => setFiles(Array.from(event.target.files || []).map((file) => file.name))} />
          <span className="font-serif mt-1 block text-sm italic text-[#545148]">
            File names are noted with the query. Upload storage is not enabled yet.
            {files.length ? ` Selected: ${files.join(", ")}` : ""}
          </span>
        </label>
        {error ? <p className="font-serif text-sm text-[#9e3924]">{error}</p> : null}
        <button className="sketch-btn sketch-btn-ink" disabled={pending} type="submit">
          {pending ? "Sending…" : "Submit query"}
        </button>
      </form>
    </div>
  );
}
