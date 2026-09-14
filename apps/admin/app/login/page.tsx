"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const requestedRole = params.get("role") === "staff" ? "staff" : "admin";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Login failed");
      if (data.user.role !== requestedRole && !(requestedRole === "staff" && data.user.role === "department_head")) {
        throw new Error(`This account is not authorized for the ${requestedRole} portal.`);
      }
      localStorage.setItem("grievx.access_token", data.access_token);
      localStorage.setItem("grievx.user", JSON.stringify(data.user));
      router.replace("/dashboard");
    } catch (err) { setError(err instanceof Error ? err.message : "Login failed"); }
    finally { setBusy(false); }
  }

  return (
    <main className="shell" style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
      <form onSubmit={submit} className="content" style={{ maxWidth: 440, width: "100%" }}>
        <p className="eyebrow">GrievX Operations</p>
        <h1>{requestedRole === "admin" ? "Admin login" : "Staff login"}</h1>
        <p className="subtle">Sign in with your authorized {requestedRole} account.</p>
        <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></label>
        <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required /></label>
        {error && <p role="alert">{error}</p>}
        <button disabled={busy} type="submit">{busy ? "Signing in…" : "Sign in"}</button>
      </form>
    </main>
  );
}
