export type SourceLink = readonly [name: string, url: string, role: string];

export const sourceLinks = [
  ["LightSpeed Git", "https://github.com/achillesromer-coder/LightSpeed", "Versioned implementation and receipts"],
  ["Type 1 Digital Review", "https://github.com/achillesromer-coder/LightSpeed/pull/46", "Draft 3D, six-view and T1-00..07 review packages"],
  ["Type 1 Römer Canon", "https://docs.google.com/spreadsheets/d/1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8/edit", "Living programme, evidence, handoff and release gates"],
  ["ACR3 Handoffs", "https://docs.google.com/spreadsheets/d/1AgAhLPNtrO91C_-ea7EdOkOsyXrCCYvFVvmDSGq8uls/edit", "Append-only cross-corpus reconciliation receipts"],
  ["LS GO Queue", "https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit", "Phone tasks, approvals, commands, results and sync health"],
  ["Portfolio Handoff", "https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit", "Cross-chat portfolio continuity"],
  ["Römer Industries", "https://romer.industries", "Reviewed public portfolio surface"],
] as const satisfies readonly SourceLink[];
