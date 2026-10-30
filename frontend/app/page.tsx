"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ApiError, api, saveSession } from "@/lib/api";
import type { TokenResponse } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  function fill(nextEmail: string, nextPassword: string) {
    setEmail(nextEmail);
    setPassword(nextPassword);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const session = await api<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      saveSession(session);
      router.push(session.user.role === "admin" ? "/admin" : "/author");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign in");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="paper-dots flex min-h-screen items-center justify-center px-4 py-10">
      <div className="sketch-card w-full max-w-md p-8 sm:p-10">
        <div className="text-center">
          <p className="font-note text-[11px] font-bold uppercase tracking-[0.28em]">BookLeaf</p>
          <h1 className="font-serif mt-3 text-4xl text-[#1c1c17]">Author support</h1>
          <p className="font-serif mt-2 text-sm italic text-[#484740]">Sign in to your books, royalties, and queries.</p>
        </div>
        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <label className="block font-note text-[11px] font-bold uppercase tracking-wider">
            Email
            <input className="sketch-input mt-1" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="block font-note text-[11px] font-bold uppercase tracking-wider">
            Password
            <input className="sketch-input mt-1" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error ? <p className="font-serif text-sm text-[#9e3924]">{error}</p> : null}
          <button className="sketch-btn sketch-btn-ink w-full py-3 text-2xl" disabled={pending} type="submit">
            {pending ? "Opening the folio…" : "Sign in"}
          </button>
        </form>
        <div className="mt-8 rounded-lg border-2 border-dashed border-[#2b2a27] bg-[#fbf8e6] p-4">
          <p className="font-note text-[11px] font-bold uppercase tracking-wider">Demo access</p>
          <button className="mt-2 block text-left font-serif text-sm text-[#2d5a27]" type="button" onClick={() => fill("priya.sharma@email.com", "Author@123")}>
            priya.sharma@email.com — author
          </button>
          <button className="mt-1 block text-left font-serif text-sm text-[#2d5a27]" type="button" onClick={() => fill("ops@bookleaf.com", "Admin@123")}>
            ops@bookleaf.com — operations desk
          </button>
        </div>
      </div>
    </main>
  );
}
