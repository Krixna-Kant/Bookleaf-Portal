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
      <h1 className="text-2xl font-semibold">My books</h1>
      <p className="mt-1 text-sm text-stone-600">Publication status, sales, and royalty position for your titles.</p>
      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
      <div className="mt-6 space-y-4">
        {books.map((book) => (
          <article key={book.id} className="rounded-2xl border border-stone-200 bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">{book.title}</h2>
                <p className="text-sm text-stone-500">
                  {book.external_book_id} · {book.genre || "Genre not set"}
                </p>
              </div>
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-900">{book.status}</span>
            </div>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <Field label="ISBN" value={book.isbn || "Not assigned yet"} />
              <Field label="Published" value={book.publication_date || "Not published"} />
              <Field label="MRP" value={book.in_production ? "Set after production" : inr(book.mrp)} />
              <Field label="Print partner" value={book.print_partner || "Not assigned"} />
              <Field label="Copies sold" value={String(book.total_copies_sold)} />
              <Field label="Royalty earned" value={inr(book.total_royalty_earned)} />
              <Field label="Royalty paid" value={inr(book.royalty_paid)} />
              <Field label="Royalty pending" value={inr(book.royalty_pending)} />
              <Field label="Last payout" value={book.last_royalty_payout_date || "No payout yet"} />
              <Field label="Per copy" value={book.author_royalty_per_copy ? inr(book.author_royalty_per_copy) : "—"} />
            </dl>
            <p className="mt-3 text-sm text-stone-600">
              {book.available_on.length ? `Listed on ${book.available_on.join(", ")}` : "Not listed yet"}
            </p>
            {book.below_payout_threshold ? (
              <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
                Pending royalty is below the ₹1,000 payout threshold, so it rolls into the next quarter.
              </p>
            ) : null}
            {!book.in_production && Number(book.royalty_pending) > 0 && !book.last_royalty_payout_date ? (
              <p className="mt-3 rounded-lg bg-orange-50 px-3 py-2 text-sm text-orange-900">
                Royalty has been earned, but no payout has been recorded yet.
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
    <div>
      <dt className="text-xs uppercase tracking-wide text-stone-500">{label}</dt>
      <dd className="mt-1">{value}</dd>
    </div>
  );
}
