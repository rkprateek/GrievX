"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{full_name:string; role:string} | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("grievx.access_token");
    const stored = localStorage.getItem("grievx.user");
    if (!token || !stored) { router.replace("/login?role=admin"); return; }
    setUser(JSON.parse(stored));
  }, [router]);

  if (!user) return <main className="content"><p>Loading…</p></main>;

  return (
    <main className="content">
      <p className="eyebrow">Authenticated dashboard</p>
      <h1>Welcome, {user.full_name}</h1>
      <p className="subtle">Role: {user.role}. Access is enforced by the API as well as this dashboard.</p>
      <div className="grid">
        <article><h2>Complaints</h2><p>Complaint operations will be added in later milestones.</p></article>
        <article><h2>Campus scope</h2><p>{user.role === "admin" ? "Campus-wide access" : "Department-level access"}</p></article>
      </div>
    </main>
  );
}
