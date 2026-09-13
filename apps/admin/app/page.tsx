const navigation = ["Overview", "Complaints", "Incidents", "Campus map", "Analytics"];

export default function HomePage() {
  return (
    <main className="shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <p className="brand">GrievX</p>
        <p className="eyebrow">Operations</p>
        <nav>
          {navigation.map((item, index) => (
            <a className={index === 0 ? "active" : ""} href="#foundation" key={item}>
              {item}
            </a>
          ))}
        </nav>
      </aside>
      <section className="content" id="foundation">
        <header>
          <p className="eyebrow">Week 2</p>
          <h1>Operations foundation</h1>
          <p className="subtle">The dashboard shell is connected by configuration to the GrievX API. Authentication and complaint data arrive in later milestones.</p>
        </header>
        <div className="grid">
          <article><h2>API</h2><p>FastAPI health endpoints are available at the configured API base URL.</p></article>
          <article><h2>Data services</h2><p>PostgreSQL, Redis, and MinIO are provisioned locally with Docker Compose.</p></article>
          <article><h2>Next milestone</h2><p>Week 3 adds authentication and role management without changing this layout foundation.</p></article>
        </div>
      </section>
    </main>
  );
}
