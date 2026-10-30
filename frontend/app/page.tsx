"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ApiError, api, saveSession } from "@/lib/api";
import type { TokenResponse } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("priya.sharma@email.com");
  const [password, setPassword] = useState("Author@123");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

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
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">BookLeaf Publishing</p>
      <h1 className="mt-2 text-3xl font-semibold">Author support</h1>
      <p className="mt-2 text-sm text-stone-600">Sign in with the email on your publishing account.</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4 rounded-2xl border border-stone-200 bg-white p-6">
        <label className="block text-sm">
          Email
          <input className="mt-1" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label className="block text-sm">
          Password
          <input className="mt-1" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button className="primary w-full" disabled={pending} type="submit">
          {pending ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="mt-4 text-xs text-stone-500">
        Demo author: priya.sharma@email.com / Author@123. Ops: ops@bookleaf.com / Admin@123.
      </p>
    </main>
  );
}
