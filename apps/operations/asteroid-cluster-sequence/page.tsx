type ClusterPanel = {
  title: string;
  source: string;
  purpose: string;
  status: string;
};

const panels: ClusterPanel[] = [
  {
    title: "Cluster sequence table",
    source: "Cluster Sequence Optimiser",
    purpose: "Show mission branch, target, class, source range, capacity, owner and status.",
    status: "data-loader pending",
  },
  {
    title: "Mining capacity model",
    source: "Mining Capacity Model",
    purpose: "Show M1-M16 capacity rule using M1 base 3 m3 and +1 m3 per added unit.",
    status: "data-loader pending",
  },
  {
    title: "Source capture status",
    source: "Mission 1 Source Capture",
    purpose: "Show source snapshot status, comparison status and conflict routing.",
    status: "data-loader pending",
  },
  {
    title: "Appendix and queue health",
    source: "Appendix & Log / Publish Review Queue",
    purpose: "Show conflict, missing-field and publish-review rows.",
    status: "data-loader pending",
  },
];

export const metadata = {
  title: "Asteroid Cluster Sequence Operations",
  description: "LightSpeed operations scaffold for asteroid target, cluster and capacity review.",
};

export default function AsteroidClusterSequencePage() {
  return (
    <main style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Asteroid Cluster Sequence Operations</h1>
      <p>
        This is a deployable scaffold for the romer.industries /operations workspace.
        It contains no secrets and expects reviewed workbook exports or an approved API/database mirror.
      </p>
      <section>
        <h2>Canonical workbook inputs</h2>
        <ul>
          <li>System Operating Register</li>
          <li>Credential Reference Register</li>
          <li>Mining Capacity Model</li>
          <li>Cluster Sequence Optimiser</li>
          <li>Mission 1 Source Capture</li>
          <li>Appendix & Log</li>
          <li>Publish Review Queue</li>
        </ul>
      </section>
      <section>
        <h2>Initial panels</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem" }}>
          {panels.map((panel) => (
            <article key={panel.title} style={{ border: "1px solid currentColor", borderRadius: "0.75rem", padding: "1rem" }}>
              <h3>{panel.title}</h3>
              <p><strong>Source:</strong> {panel.source}</p>
              <p>{panel.purpose}</p>
              <p><strong>Status:</strong> {panel.status}</p>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h2>Guardrails</h2>
        <ul>
          <li>No plaintext secret values in the repo or workbook.</li>
          <li>Drive remains the durable workbook/source layer until a database mirror is active.</li>
          <li>Public outputs route through Publish Review Queue.</li>
          <li>Write-back is deferred until audit and queue logic exist.</li>
        </ul>
      </section>
    </main>
  );
}
