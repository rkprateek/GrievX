"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [requestedRole, setRequestedRole] = useState<"admin" | "staff">("admin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const role = new URLSearchParams(window.location.search).get("role");
    setRequestedRole(role === "staff" ? "staff" : "admin");
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(API_BASE_URL + "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Login failed");
      if (data.user.role !== requestedRole && !(requestedRole === "staff" && data.user.role === "department_head")) {
        throw new Error("This account is not authorized for the " + requestedRole + " portal.");
      }
      localStorage.setItem("grievx.access_token", data.access_token);
      localStorage.setItem("grievx.user", JSON.stringify(data.user));
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <form onSubmit={submit} className="content login-card">
        <div className="brand-lockup login-brand"><span className="brand-mark">G</span><div><strong>GrievX</strong><span>Operations</span></div></div>
        <p className="eyebrow">{requestedRole === "admin" ? "Administrator portal" : "Staff portal"}</p>
        <h1>{requestedRole === "admin" ? "Admin login" : "Staff login"}</h1>
        <p className="subtle">Sign in with your authorized {requestedRole} account.</p>
        <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required autoComplete="email" /></label>
        <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required autoComplete="current-password" /></label>
        {error && <p className="login-error" role="alert">{error}</p>}
        <button className="primary-button full" disabled={busy} type="submit">{busy ? "Signing in…" : "Sign in"}</button>
      </form>
    </main>
  );
}
