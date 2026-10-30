"use client";

import { useEffect, useState } from "react";
import { api, inr } from "@/lib/api";
import type { Book } from "@/lib/types";

export default function BooksPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Book[]>("/api/v1/books").then(setBooks).catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <p className="font-note text-[11px] uppercase tracking-wider text-[#825c18]">Catalog</p>
      <h1 className="font-hand text-6xl leading-none">My books</h1>
      <p className="font-serif mt-2 italic text-[#545148]">Titles, print status, and the royalty ledger on your account.</p>
      {error ? <p className="mt-4 font-serif text-sm text-[#9e3924]">{error}</p> : null}
      <div className="mt-8 space-y-6">
        {books.map((book) => (
          <article key={book.id} className={book.in_production ? "rounded-lg border-2 border-dashed border-[#79776f] bg-[#faf6ec] p-6" : "sketch-card p-6"}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-note text-[11px] uppercase tracking-wider text-[#545148]">
                  {book.external_book_id} · {book.genre || "Genre not set"}
                </p>
                <h2 className="font-serif mt-1 text-3xl">{book.title}</h2>
              </div>
              <span className={`rounded-full border border-[#2b2a27] px-3 py-1 font-note text-[11px] font-bold ${book.in_production ? "crayon-ochre" : "crayon-sage"}`}>
                {book.status}
              </span>
            </div>
            <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Field label="ISBN" value={book.isbn || "Not assigned yet"} />
              <Field label="Published" value={book.publication_date || "Not published"} />
              <Field label="MRP" value={book.in_production ? "Set after production" : inr(book.mrp)} />
              <Field label="Print partner" value={book.print_partner || "Not assigned"} />
              <Field label="Copies sold" value={String(book.total_copies_sold)} />
              <Field label="Royalty earned" value={book.in_production ? "—" : inr(book.total_royalty_earned)} />
              <Field label="Royalty paid" value={book.in_production ? "—" : inr(book.royalty_paid)} />
              <Field label="Royalty pending" value={book.in_production ? "—" : inr(book.royalty_pending)} />
              <Field label="Last payout" value={book.last_royalty_payout_date || "No payout yet"} />
              <Field label="Per copy" value={book.author_royalty_per_copy ? inr(book.author_royalty_per_copy) : "—"} />
            </dl>
            <p className="font-serif mt-4 text-sm">{book.available_on.length ? `Listed on ${book.available_on.join(", ")}` : "Not listed yet"}</p>
            {book.in_production ? (
              <p className="font-hand mt-3 text-2xl text-[#825c18]">Royalty ledger stays quiet until the book is published and selling.</p>
            ) : null}
            {book.below_payout_threshold ? (
              <p className="mt-3 rounded-lg border border-[#2b2a27] bg-[#fff2b2] px-3 py-2 font-serif text-sm">
                Pending royalty is below ₹1,000, so it rolls into the next quarter.
              </p>
            ) : null}
            {!book.in_production && Number(book.royalty_pending) > 0 && !book.last_royalty_payout_date ? (
              <p className="mt-3 rounded-lg border border-[#2b2a27] bg-[#ffd6cc] px-3 py-2 font-serif text-sm">
                Royalty has been earned, and no payout has been recorded yet.
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#2b2a27]/30 bg-[#fffdf8] p-3">
      <dt className="font-note text-[10px] uppercase tracking-wider text-[#545148]">{label}</dt>
      <dd className="font-serif mt-1 text-sm">{value}</dd>
    </div>
  );
}
