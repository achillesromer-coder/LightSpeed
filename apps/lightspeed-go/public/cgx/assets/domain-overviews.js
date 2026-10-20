// Public descriptive programme families ONLY; not sourced private CGX records.
// This is a non-authoritative synthetic index pending owner publication review.
export const PUBLIC_DOMAIN_SCHEMA = "unispace-cgx-domain-orientation/1";
const families = Object.freeze({
  romer: Object.freeze({
    label: "Römer-Grex",
    heading: "Engineering & infrastructure research",
    parent: "Cognigrex.cgx / Romer.cgx",
    description: "Programme-level views of systems engineering, resilient infrastructure and interplanetary logistics research. Simulations, designs and physical demonstrations retain separate qualification.",
    entries: Object.freeze([
      ["Mark systems", "Modular mission and spacecraft architectures"],
      ["Solar Hull", "Spacecraft-integrated energy-material research"],
      ["RFS / EMFF", "Electromagnetic interaction and routing research"],
      ["Luke / Inter-Sol", "Transfer, recovery and relay facility concepts"],
      ["South-East Queensland corridor", "Parametric civil-infrastructure and ecological interface concepts"]
    ])
  }),
  eco: Object.freeze({
    label: "Eco-Grex",
    heading: "Ecology & regenerative systems research",
    parent: "Cognigrex.cgx / Eco.cgx",
    description: "Programme-level ecological knowledge, monitoring and restoration planning. Site, species, intervention and outcome claims require attributable field evidence.",
    entries: Object.freeze([
      ["Habitat and species", "Site-specific evidence and conservation constraints"],
      ["Ecological monitoring", "Measurements, provenance and uncertainty over time"],
      ["Bio-blocks and material pathways", "Candidate materials and qualified process interfaces"],
      ["Second Cycle", "Circularity and resource rehabilitation research"],
      ["Infrastructure/ecology interface", "Context-sensitive civil and environmental overlays"]
    ])
  })
});
export const PUBLIC_DOMAINS = families;
export function selectDomain(name) {
  return Object.hasOwn(families, name) ? families[name] : null;
}
export function describeDomain(name) {
  const item = selectDomain(name);
  if (!item) return { status:"UNKNOWN_DOMAIN", published:false };
  return {
    schema:PUBLIC_DOMAIN_SCHEMA, label:item.label, heading:item.heading,
    description:item.description, families:item.entries.map(([title,description])=>({title,description})),
    evidence:"PROGRAMME_DESCRIPTIVE_ONLY", authority:"PUBLIC_SYNTHETIC_ORIENTATION",
    object_id:null, signed_owner_release_verified:false, physical_qualification:false,
    authenticated:false, private_catalogue_included:false, public_release_proven:false
  };
}
