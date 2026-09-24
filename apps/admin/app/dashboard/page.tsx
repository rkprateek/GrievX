"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type Complaint = {
  id: string;
  description: string;
  status: string;
  priority: string;
  created_at: string;
  updated_at: string;
  student?: { full_name: string; email: string } | null;
  department?: { name: string } | null;
  assigned_staff?: { full_name: string } | null;
  history: Array<{ from_status?: string | null; to_status: string; created_at: string }>;
};

type Overview = {
  total: number;
  submitted: number;
  assigned: number;
  in_progress: number;
  resolved: number;
  closed: number;
  rejected: number;
};

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const WS = API.replace(/\/api\/v1\/?$/, "").replace(/^http/, "ws");

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [user, setUser] = useState<{ full_name: string; role: string } | null>(null);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [selected, setSelected] = useState<Complaint | null>(null);
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [live, setLive] = useState(false);

  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  const load = useCallback(async () => {
    if (!token) return;
    setError("");
    try {
      const [overviewResponse, complaintsResponse] = await Promise.all([
        fetch(`${API}/admin/overview`, { headers }),
        fetch(`${API}/admin/complaints?sort=updated_at&order=desc`, { headers }),
      ]);
      if (!overviewResponse.ok || !complaintsResponse.ok) throw new Error("Unable to load complaint operations data.");
      setOverview(await overviewResponse.json());
      const rows = await complaintsResponse.json() as Complaint[];
      setComplaints(rows);
      setSelected((current) => current ? rows.find((row) => row.id === current.id) ?? current : rows[0] ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load dashboard.");
    } finally {
      setLoading(false);
    }
  }, [headers, token]);

  useEffect(() => {
    const storedToken = localStorage.getItem("grievx.access_token");
    const storedUser = localStorage.getItem("grievx.user");
    if (!storedToken || !storedUser) {
      router.replace("/login?role=admin");
      return;
    }
    setToken(storedToken);
    setUser(JSON.parse(storedUser));
  }, [router]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!token) return;
    const socket = new WebSocket(`${WS}/ws/notifications?token=${encodeURIComponent(token)}`);
    socket.onopen = () => setLive(true);
    socket.onclose = () => setLive(false);
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as { type?: string; complaint_id?: string };
        if (message.type === "notification") void load();
      } catch {
        // Ignore malformed realtime frames.
      }
    };
    const fallback = window.setInterval(() => void load(), 15000);
    return () => {
      window.clearInterval(fallback);
      socket.close();
    };
  }, [load, token]);

  async function changeStatus() {
    if (!selected || !status || status === selected.status) return;
    setError("");
    try {
      const response = await fetch(`${API}/admin/complaints/${encodeURIComponent(selected.id)}/status`, {
        method: "PATCH",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail ?? "Status update failed.");
      setSelected(data);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Status update failed.");
    }
  }

  const filtered = complaints.filter((item) => {
    const needle = query.trim().toLowerCase();
    return !needle || item.id.toLowerCase().includes(needle) || item.description.toLowerCase().includes(needle);
  });

  if (!user || loading) return <main className="loading-page"><p>Loading operations dashboard…</p></main>;

  return (
    <div className="admin-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><span className="brand-mark">G</span><div><strong>GrievX</strong><span>Campus operations</span></div></div>
        <nav className="side-nav">
          <a className="active" href="/dashboard">Complaints</a>
          <a href="#notifications">Notifications</a>
        </nav>
        <div className="sidebar-footer"><div className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</div><div><strong>{user.full_name}</strong><span>{user.role}</span></div></div>
      </aside>

      <main className="admin-main">
        <div className="topbar">
          <div><p className="eyebrow">Week 6 · Lifecycle</p><h1>Complaint operations</h1><p className="subtle">Status changes are persisted, notified, and reflected in realtime.</p></div>
          <div className="topbar-actions"><span className="scope-pill">{live ? "● Live updates" : "○ Reconnecting"}</span><button className="ghost-button" onClick={() => { localStorage.removeItem("grievx.access_token"); localStorage.removeItem("grievx.user"); router.replace("/login?role=admin"); }}>Sign out</button></div>
        </div>

        {error && <div className="alert">{error}</div>}

        <section className="stats-grid">
          {[
            ["Total", overview?.total ?? 0], ["Submitted", overview?.submitted ?? 0],
            ["Assigned", overview?.assigned ?? 0], ["In progress", overview?.in_progress ?? 0],
            ["Resolved", overview?.resolved ?? 0], ["Closed", overview?.closed ?? 0],
          ].map(([label, value]) => <article className="stat-card" key={String(label)}><span>{label}</span><strong>{value}</strong><small>Live from complaint state</small></article>)}
        </section>

        <section className="workspace">
          <article className="panel queue-panel">
            <div className="panel-header"><div><p className="eyebrow">Complaint queue</p><h2>Current complaints <span className="count-badge">{filtered.length}</span></h2></div><button className="ghost-button" onClick={() => void load()}>Refresh</button></div>
            <div className="filters"><div className="search-box"><span>⌕</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search complaint ID or description" /></div></div>
            <div className="table-wrap">
              <table><thead><tr><th>Complaint</th><th>Department</th><th>Status</th><th>Priority</th><th>Updated</th></tr></thead>
                <tbody>{filtered.map((item) => <tr key={item.id} className={selected?.id === item.id ? "selected-row" : ""} onClick={() => { setSelected(item); setStatus(item.status); }}>
                  <td><strong>{item.id}</strong><span>{item.description}</span></td>
                  <td>{item.department?.name ?? "Unassigned"}</td>
                  <td><span className={`status-badge status-${item.status.toLowerCase()}`}>{item.status.replace("_", " ")}</span></td>
                  <td>{item.priority}</td>
                  <td>{new Date(item.updated_at).toLocaleString()}</td>
                </tr>)}</tbody>
              </table>
              {filtered.length === 0 && <div className="empty-state"><strong>No complaints found</strong><span>Try a different search.</span></div>}
            </div>
          </article>

          <article className="panel detail-panel">
            {!selected ? <div className="detail-empty"><h2>Select a complaint</h2><p>Choose a complaint to inspect its lifecycle and change its status.</p></div> : <>
              <div className="detail-header"><div><p className="eyebrow">Complaint detail</p><h2>{selected.id}</h2><p>{selected.student?.full_name ?? "Student"} · {selected.student?.email ?? "No email"}</p></div><span className={`status-badge status-${selected.status.toLowerCase()}`}>{selected.status}</span></div>
              <div className="detail-section"><span className="detail-label">Description</span><p className="description">{selected.description}</p></div>
              <div className="detail-grid"><div><span className="detail-label">Department</span><strong>{selected.department?.name ?? "Unassigned"}</strong></div><div><span className="detail-label">Assigned staff</span><strong>{selected.assigned_staff?.full_name ?? "Unassigned"}</strong></div></div>
              <div className="detail-section control-card"><span className="detail-label">Update status</span><select value={status || selected.status} onChange={(e) => setStatus(e.target.value)}><option value="SUBMITTED">SUBMITTED</option><option value="ASSIGNED">ASSIGNED</option><option value="IN_PROGRESS">IN_PROGRESS</option><option value="RESOLVED">RESOLVED</option><option value="CLOSED">CLOSED</option><option value="REJECTED">REJECTED</option></select><button className="primary-button full" disabled={!status || status === selected.status} onClick={() => void changeStatus()}>Save status</button></div>
              <div className="detail-section"><div className="section-heading"><span>Status timeline</span><small>Every transition is recorded</small></div><div className="timeline">{selected.history.map((entry, index) => <div className="timeline-item" key={`${entry.created_at}-${index}`}><span className="timeline-dot" /><div><strong>{entry.from_status ? `${entry.from_status} → ${entry.to_status}` : entry.to_status}</strong><small>{new Date(entry.created_at).toLocaleString()}</small></div></div>)}</div></div>
            </>}
          </article>
        </section>
      </main>
    </div>
  );
}
