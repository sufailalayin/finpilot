const cards = [
  ["Users", "—"],
  ["Active trials", "—"],
  ["Paid subscribers", "—"],
  ["Monthly revenue", "—"],
  ["AI requests", "—"],
];

export default function AdminDashboard() {
  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: 32 }}>
      <p style={{ marginBottom: 4 }}>Hastron Ventures</p>
      <h1 style={{ marginTop: 0 }}>FinPilot Admin</h1>
      <p>User, subscription and platform analytics will appear here.</p>
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16,
          marginTop: 32,
        }}
      >
        {cards.map(([label, value]) => (
          <article
            key={label}
            style={{ border: "1px solid #ddd", borderRadius: 16, padding: 20 }}
          >
            <small>{label}</small>
            <h2>{value}</h2>
          </article>
        ))}
      </section>
    </main>
  );
}
