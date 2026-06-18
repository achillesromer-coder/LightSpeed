export type StatusState = "canonical" | "bounded-assumption" | "known-unknown";

export type SpaceportZone = {
  name: string;
  radiusM: number;
  description: string;
};

export type FacilityRecord = {
  id: string;
  name: string;
  footprint: string;
  elevation: string;
  releaseStatus: StatusState;
  notes: string;
};

export const twinZones: SpaceportZone[] = [
  {
    name: "Central Facility Boundary",
    radiusM: 2500,
    description: "All facilities and buildings remain inside this radius.",
  },
  {
    name: "Active Eco-Restoration",
    radiusM: 3500,
    description: "1 km active band for managed biome, native rehabilitation, and functional climate pockets.",
  },
  {
    name: "Passive Eco-Restoration",
    radiusM: 11000,
    description: "Outer passive restoration reserve securing the full radial print.",
  },
];

export const facilityRecords: FacilityRecord[] = [
  {
    id: "integration-hall",
    name: "Integration Hall",
    footprint: "40 m x 75 m, 22 m clear",
    elevation: "+1.5 m floor, +8% beveled foundation",
    releaseStatus: "canonical",
    notes: "Starship-compatible roller doors both ends; single bridge crane spans the hall.",
  },
  {
    id: "chainhill",
    name: "ChainHill Relay",
    footprint: "~225-250 m relay length",
    elevation: "flat raised concrete, approximately 3 m above water table",
    releaseStatus: "bounded-assumption",
    notes: "Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.",
  },
  {
    id: "x-pads",
    name: "X-Layout Pads",
    footprint: "solid pads, no beveled building base",
    elevation: "pad-specific hardstand",
    releaseStatus: "canonical",
    notes: "Flame/exhaust outlets orient away from central node and buildings.",
  },
  {
    id: "mission-control",
    name: "Mission Control / ATC",
    footprint: "pentagon base, level 1 at 80%, four-storey tower",
    elevation: "+1.5 m floor, +8% beveled foundation",
    releaseStatus: "canonical",
    notes: "Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.",
  },
  {
    id: "living-rd",
    name: "R&D + Living Quarters",
    footprint: "room-level workbook detail pending",
    elevation: "+1.5 m floor, +8% beveled foundation",
    releaseStatus: "known-unknown",
    notes: "FIFO and FIFO+family support with ground community and rooftop lifestyle zones.",
  },
];

export const workbookTabs = [
  "site_zones",
  "facilities",
  "rooms_spaces",
  "roads_tracks",
  "pads_exhaust",
  "eco_restoration",
  "standards_evidence",
  "viewer_toggles",
  "known_unknowns",
];

