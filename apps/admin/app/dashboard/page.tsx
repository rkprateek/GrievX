"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type Complaint = {
  id: string;
  description: string;
  status: string;
  priority: string;
  department?: { id: number; name: string; code: string } | null;
  assigned_staff?: { id: string; full_name: string; email: string; department_id?: number | null } | null;
  student?: { id: string; full_name: string; email: string; department?: string | null } | null;
  history: Array<{ from_status?: string | null; to_status: string; created_at: string }>;
  created_at: string;
  updated_at: string;
};

type User = { id: string; full_name: string; role: string };

const STATUS_ORDER = ["SUBMITTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"];
const TRANSITIONS: Record<string, string[]> = {
  SUBMITTED: ["ASSIGNED"],
  ASSIGNED: ["IN_PROGRESS"],
  IN_PROGRESS: ["RESOLVED"],
  RESOLVED: ["CLOSED", "IN_PROGRESS"],
  CLOSED: [],
};

async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    ...init,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail ?? `Request failed (${response.status})`);
  return data as T;
}

function websocketUrl(token: string) {
  return `${API_BASE_URL.replace(/^http/, "ws")}/ws/notifications?token=${encodeURIComponent(token)}`;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState("");
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [selected, setSelected] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [live, setLive] = useState(false);

  const load = useCallback(async (accessToken: string, keepSelection = true) => {
    const rows = await api<Complaint[]>("/admin/complaints?sort=updated_at&order=desc", accessToken);
    setComplaints(rows);
    if (keepSelection) {
      setSelected((current) => {
        if (!current) return rows[0] ?? null;
        return rows.find((item) => item.id === current.id) ?? current;
      });
    } else {
      setSelected(rows[0] ?? null);
    }
  }, []);

  useEffect(() => {
    const accessToken = localStorage.getItem("grievx.access_token");
    const stored = localStorage.getItem("grievx.user");
    if (!accessToken || !stored) {
      router.replace("/login?role=admin");
      return;
    }
    setToken(accessToken);
    setUser(JSON.parse(stored));
    setLoading(true);
    load(accessToken, false).catch((err) => setError(err instanceof Error ? err.message : "Unable to load complaints")).finally(() => setLoading(false));
  }, [load, router]);

  useEffect(() => {
    if (!token) return;
    const socket = new WebSocket(websocketUrl(token));
    socket.onopen = () => setLive(true);
    socket.onclose = () => setLive(false);
    socket.onerror = () => setLive(false);
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.event === "complaint.updated") {
          void load(token);
        }
      } catch {
        // Ignore malformed real-time payloads.
      }
    };
    return () => socket.close();
  }, [token, load]);

  useEffect(() => {
    if (!token) return;
    const fallback = window.setInterval(() => void load(token), 10000);
    return () => window.clearInterval(fallback);
  }, [token, load]);

  const counts = useMemo(() => {
    const result: Record<string, number> = {};
    for (const status of STATUS_ORDER) result[status] = complaints.filter((item) => item.status === status).length;
    return result;
  }, [complaints]);

  async function changeStatus(nextStatus: string) {
    if (!selected || !token) return;
    setSaving(true);
    setError("");
    try {
      const updated = await api<Complaint>(`/admin/complaints/${encodeURIComponent(selected.id)}/status`, token, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      });
      setSelected(updated);
      setComplaints((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to change status");
    } finally {
      setSaving(false);
    }
  }

  function signOut() {
    localStorage.removeItem("grievx.access_token");
    localStorage.removeItem("grievx.user");
    router.replace("/login?role=admin");
  }

  if (!user || loading) return <main className="loading-page">Loading operations dashboard…</main>;

  return (
    <div className="admin-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><span className="brand-mark">G</span><div><strong>GrievX</strong><span>Operations</span></div></div>
        <nav className="side-nav"><a className="active" href="#complaints">Complaints</a><a href="#timeline">Lifecycle</a><a href="#notifications">Real-time</a></nav>
        <div className="sidebar-footer"><div className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</div><div><strong>{user.full_name}</strong><span>{user.role}</span></div></div>
      </aside>

      <main className="admin-main">
        <header className="topbar">
          <div><p className="eyebrow">Complaint operations</p><h1>Lifecycle control</h1></div>
          <div className="topbar-actions">
            <span className="scope-pill">{live ? "● Live" : "○ Reconnecting"} · {user.role}</span>
            <button className="ghost-button" onClick={signOut}>Sign out</button>
          </div>
        </header>

        {error && <div className="alert" role="alert">{error}</div>}

        <section className="stats-grid">
          <article className="stat-card stat-blue"><span>Total</span><strong>{complaints.length}</strong><small>Visible complaints</small></article>
          <article className="stat-card stat-amber"><span>Submitted</span><strong>{counts.SUBMITTED}</strong><small>Awaiting assignment</small></article>
          <article className="stat-card stat-violet"><span>In progress</span><strong>{counts.IN_PROGRESS}</strong><small>Being worked on</small></article>
          <article className="stat-card stat-green"><span>Resolved</span><strong>{counts.RESOLVED}</strong><small>Ready for closure</small></article>
        </section>

        <section id="complaints" className="workspace">
          <div className="panel queue-panel">
            <div className="panel-header">
              <div><p className="eyebrow">Live queue</p><h2>Complaints <span className="count-badge">{complaints.length}</span></h2></div>
              <button className="ghost-button" onClick={() => void load(token)}>Refresh</button>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Complaint</th><th>Reporter</th><th>Status</th><th>Priority</th><th>Updated</th></tr></thead>
                <tbody>
                  {complaints.map((item) => (
                    <tr key={item.id} className={selected?.id === item.id ? "selected-row" : ""} onClick={() => setSelected(item)}>
                      <td><strong>{item.id}</strong><span>{item.description.slice(0, 52)}{item.description.length > 52 ? "…" : ""}</span></td>
                      <td>{item.student?.full_name ?? "Student"}</td>
                      <td><span className={`status-badge status-${item.status.toLowerCase()}`}>{item.status.replace("_", " ")}</span></td>
                      <td><span className={`priority-badge priority-${item.priority.toLowerCase()}`}>{item.priority}</span></td>
                      <td>{new Date(item.updated_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {complaints.length === 0 && <div className="empty-state"><strong>No complaints in your scope</strong><span>New lifecycle events will appear here automatically.</span></div>}
            </div>
          </div>

          <aside className="panel detail-panel">
            {!selected ? <div className="detail-empty"><h2>Select a complaint</h2><p>Choose a complaint to inspect its lifecycle and update the current state.</p></div> : (
              <>
                <div className="detail-header"><div><p className="eyebrow">Complaint detail</p><h2>{selected.id}</h2><p>{selected.student?.full_name} · {selected.student?.email}</p></div><span className={`status-badge status-${selected.status.toLowerCase()}`}>{selected.status.replace("_", " ")}</span></div>
                <div className="detail-section"><span className="detail-label">Description</span><p className="description">{selected.description}</p></div>
                <div className="detail-section control-card"><span className="detail-label">Update status</span><select disabled={saving || TRANSITIONS[selected.status]?.length === 0} value="" onChange={(event) => { if (event.target.value) void changeStatus(event.target.value); }}><option value="">Select next status…</option>{(TRANSITIONS[selected.status] ?? []).map((next) => <option key={next} value={next}>{next.replace("_", " ")}</option>)}</select>{saving && <small>Saving lifecycle update…</small>}</div>
                <div id="timeline" className="detail-section"><div className="section-heading"><span>Complaint timeline</span><small>Every status change is recorded</small></div><div className="timeline">{selected.history.map((entry, index) => <div className="timeline-item" key={`${entry.to_status}-${entry.created_at}-${index}`}><span className="timeline-dot" /><div><strong>{entry.from_status ? `${entry.from_status} → ${entry.to_status}` : entry.to_status}</strong><small>{new Date(entry.created_at).toLocaleString()}</small></div></div>)}</div></div>
                <div id="notifications" className="detail-section"><div className="section-heading"><span>Real-time updates</span><small>{live ? "WebSocket connected" : "Polling fallback active"}</small></div><div className="muted-box">When this complaint changes, the dashboard refreshes automatically without a page reload.</div></div>
              </>
            )}
          </aside>
        </section>
      </main>
    </div>
  );
}
