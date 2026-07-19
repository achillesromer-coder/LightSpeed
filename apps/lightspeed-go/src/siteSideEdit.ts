type SiteIntegrationManifest = {
  schema_version: string;
  site_name: string;
  edit_mode: string;
  create_new_site: boolean;
  publish_state: string;
  authority_chain: string[];
  current_views: string[];
  promoted_components: string[];
  deferred_components: string[];
};

const manifestUrl = new URL("./data/site_integration.json", document.baseURI).toString();

const loadManifest = async (): Promise<SiteIntegrationManifest | null> => {
  try {
    const response = await fetch(manifestUrl, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as SiteIntegrationManifest;
  } catch {
    return null;
  }
};

const injectStyles = (): void => {
  if (document.getElementById("lsgo-sites-side-edit-styles")) return;
  const style = document.createElement("style");
  style.id = "lsgo-sites-side-edit-styles";
  style.textContent = `
    .site-context-strip { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .site-context-strip span { border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:var(--muted); font-size:12px; background:rgba(255,255,255,.025); }
    .site-context-strip strong { color:var(--text); }
    .site-parity-card { border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(255,255,255,.025); display:grid; gap:8px; }
    .site-parity-card p { margin:0; color:var(--muted); line-height:1.5; }
    .site-parity-card .site-chain { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
    .site-parity-card .site-chain span { border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; }
    .site-parity-card .site-chain i { color:var(--teal); font-style:normal; }
  `;
  document.head.appendChild(style);
};

const mount = async (): Promise<boolean> => {
  const topbar = document.querySelector<HTMLElement>(".topbar > div:first-child");
  const sources = document.querySelector<HTMLElement>("#view-sources");
  if (!topbar || !sources) return false;

  injectStyles();
  const manifest = await loadManifest();
  const authority = manifest?.authority_chain ?? [
    "Nathaniel Bower",
    "Achilles / GO gate",
    "agent floor",
    "LightSpeed Desktop",
    "Git and Drive receipts",
  ];

  if (!document.getElementById("site-context-strip")) {
    const strip = document.createElement("div");
    strip.id = "site-context-strip";
    strip.className = "site-context-strip";
    strip.innerHTML = `
      <span><strong>Owner:</strong> Nathaniel Bower</span>
      <span><strong>Mode:</strong> existing Site side edit</span>
      <span><strong>Source:</strong> Git + Drive aligned</span>
    `;
    topbar.appendChild(strip);
  }

  if (!document.getElementById("site-parity-card")) {
    const card = document.createElement("article");
    card.id = "site-parity-card";
    card.className = "panel site-parity-card";
    card.innerHTML = `
      <p class="eyebrow">Current Site integration</p>
      <h2>One surface, additive side edit</h2>
      <p>The existing LightSpeed GO Site remains canonical. Git carries implementation, Drive carries evidence and control records, and Sites publishes only the reviewed delta.</p>
      <div class="site-chain">
        ${authority.map((item, index) => `${index ? "<i>→</i>" : ""}<span>${item}</span>`).join("")}
      </div>
      <p><strong>Publish state:</strong> ${manifest?.publish_state ?? "review-required"}. No replacement Site is created.</p>
    `;
    sources.prepend(card);
  }

  return true;
};

let attempts = 0;
const mountWhenReady = (): void => {
  void mount().then((mounted) => {
    if (mounted || attempts >= 40) return;
    attempts += 1;
    window.requestAnimationFrame(mountWhenReady);
  });
};

mountWhenReady();
