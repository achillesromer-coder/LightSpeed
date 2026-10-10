import { bindMeshViewerTriggers, meshViewerButtonMarkup } from "./meshViewer";\nimport { bindComponentPlateTriggers, componentPlateButtonMarkup } from "./componentVisualizer";

export type ReviewObject = {
  id: string;
  label: string;
  role: string;
  level: string;
  source: string;
  render: string;
  hero_render?: string;
  mesh_data?: string;
  source_sha256?: string;
  render_state?: string;
  geometry_state: string;
  physical_state: string;
  review_rules: string[];
  stats?: { vertices: number; faces: number; extents: number[]; bytes: number };
};

export type ComponentAtlasRecord = {