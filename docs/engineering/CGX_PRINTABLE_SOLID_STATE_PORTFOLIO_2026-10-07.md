# CGX Printable Solid-State Portfolio — Convergence Note

**Date:** 2026-10-07  
**State:** review implementation; Drive-owned engineering/evidence canon remains authoritative  
**Scope:** Cognigrex/.cgx + Römer-Grex + Eco-Grex + LightSpeed + Raphael/UTP convergence

## 1. Core architectural move

The useful unit is not required to be a miniature smartphone. A physical object can be a **thin CGX endpoint**: stable identity, capability manifest, small local state, sensing/actuation interfaces and a signed handshake. Heavy computation may be delegated to an authenticated Cognigrex/LightSpeed node under the existing lease/readback contract.

This changes the design question from “can every object carry a full processor stack?” to:

> What is the minimum local material geometry, identity, sensing, actuation and safety logic that lets this object participate in a larger verified compute and manufacturing graph?

The endpoint remains useful only within the capabilities actually available to it. Network-equivalent system functionality is not a claim of smartphone-class onboard compute, semiconductor density or standalone performance.

## 2. The three neutral interfaces

| Plane | Owns | Typical objects | Required handshake |
|---|---|---|---|
| Filespace | identity, semantics, configuration, provenance, recipes, evidence refs | .cgx objects, BOM/BOP/BOC, material passports, tests | stable ID + hash + authority/evidence ceiling |
| Dataspace | live state, telemetry, solver inputs/results, execution requests, alerts | sensor streams, process state, simulation/optimizer results | scoped lease + verified input + readback receipt |
| Solid-state / physical | material layers, geometry, interfaces, sensing and actuation | printed/hybrid devices, coatings, structures, process cells | configuration binding + qualification state + safe actuation gate |

A DBR closes the loop: **Snapshot -> Hash -> Handshake -> Execute/Test -> Readback -> Receipt -> Reviewed Promotion**.

“New neutral” therefore means a portable typed interface across representations. It does **not** mean that arbitrary materials or processes are physically interchangeable.

## 3. Printable technology catalogue

The Drive-owned catalogue now carries PT-071…PT-081 as the new convergence set, on top of the existing PT-001…PT-070 primitives.

| ID | Portfolio object | Primary role | Initial evidence ceiling |
|---|---|---|---|
| PT-071 | Thin .cgx identity endpoint | identity + capability + delegated compute bridge | architecture / bench candidate |
| PT-072 | Function-as-geometry/material stack | compile requested function into qualified layers/interfaces/process | digital architecture |
| PT-073 | Structural energy shell + cavity | structure + distributed storage + thermal/shielding | R&D architecture |
| PT-074 | Eco-Grex recovered functional-feed loop | cleanup stream -> passported feed or reject | Eco-coupled extension |
| PT-075 | Functional road/building coating stack | protective/optical/electrical/heating/sensing surface | R&D architecture |
| PT-076 | Local-horizon capability compiler | local recipes + safe fallback + minimum imports | implementation scaffold |
| PT-077 | Minimum-skeleton bootstrap production cell | seed outpost/industrial expansion scenario | founder scenario / frontier |
| PT-078 | Debris tag / safeguard node | identity + tracking + hazard envelope | Project-C bridge architecture |
| PT-079 | CGX DIY/pro build assistant | human interface, assembly, validation, troubleshooting | implementation architecture |
| PT-080 | Filespace-Dataspace-Solid-state bridge | one lineage across all three planes | implementation contract |
| PT-081 | Recursive modular printer/tooling expansion | qualified child process-cell growth | R&D architecture |

These additions deliberately reuse the existing primitive library: structural elements, seals/cavities, thermal breaks, sensors, battery/supercapacitor candidates, printed logic/memory, hybrid compute islands, RFID/NFC identity, circular feeds, regolith/local metal structures, Mark integrated bodies, Luke/InterSol support modules and the roaming UTP.

## 4. “Print a technology” is a compiler problem

For a requested function (F^*), CGX should search the bounded design space of:

- qualified materials and feedstocks;
- layer order and interfaces;
- printable/depositable geometry and manufacturing resolution;
- local environment and process micro-envelopes;
- seed components that cannot yet be produced locally;
- energy, mass, waste, contamination, maintenance and lifecycle constraints;
- evidence and authority ceilings.

A generic objective can be expressed as:

[
min J = w_f |\hat F(m,g,p,e)-F^*|^2 + w_m M + w_E E + w_W W + w_R R
]

subject to hard material, process, environment, safety, ecology, rights, authority and evidence constraints.

The output is **not automatically a build approval**. It is a candidate stack, uncertainty envelope and verification plan.

## 5. Structural energy shell

The external shell can be treated as an active multifunctional region rather than dead enclosure mass. Candidate architectures include:

- conductive current-collector paths;
- carbon/graphene or other measured electrode structures;
- dielectric/separator layers;
- qualified electrolyte/ionic medium where an electrochemical cell is used;
- cavities for working volume, thermal isolation, pressure management or field geometry;
- shielding and structural load paths.

The energy model must remain physically conventional: capacitor energy (U=\tfrac12CV^2), electrochemical energy follows the material/cell state and voltage, and structural performance remains independently verified. **Void/free space is never an energy source.**

## 6. Local-horizon manufacturing

A “local horizon” is the bounded resource-and-capability environment visible to a node. The same grammar applies at different scales:

- **Terrestrial:** local utilities, recycled materials, suppliers, workshops, regulations.
- **Ocean:** recovered streams, corrosion/salt/biosecurity constraints, mobile/shore process cells.
- **Orbit:** transported stocks, recovered mission hardware, debris/object state, microgravity/vacuum effects.
- **Lunar/Martian/Asteroid:** assayed regolith/body material, solar/other available energy, limited seed inventory, dust/thermal/vacuum constraints.
- **Interplanetary/interstellar:** federated nodes with delayed communications, larger autonomy requirements and explicit safe degraded states.

The compiler objective is capability sufficiency with minimum imported mass and avoidable waste—not maximum extraction.

## 7. Eco-Grex material closure

Cleanup becomes an input opportunity only after qualification:

1. collect and preserve source/provenance;
2. sort and separate streams;
3. decontaminate;
4. assay composition and uncertainty;
5. test leachate/corrosion/toxicity/biosecurity/processability as applicable;
6. issue a material passport;
7. formulate a feed;
8. print a coupon;
9. promote only to applications whose acceptance criteria pass;
10. recycle/recover/reject any unsafe fraction.

This supports plastics, metals, carbonaceous material, glass/minerals and bio-derived binders without treating “recycled” as an automatic quality or safety claim.

## 8. Functional coatings and infrastructure

The same material/geometric compiler can target surfaces rather than freestanding devices. Candidate 2–3+ layer road/building/habitat systems include:

- protective/weathering layer;
- reflective/optical layer;
- conductive/resistive-heating layer;
- embedded or patterned strain, moisture, temperature or electrochemical sensing;
- RF/EM/antenna patterns;
- repair/diagnostic identity layer.

Geospatial feedback can alter inspection, heating, lighting, drainage or maintenance actions. Any proposed biological/resonant effect must remain a separately defined, measurable hypothesis; no health or biological efficacy is inherited from the control architecture.

## 9. Bootstrap scenario

The founder scenario is retained as a design case:

- three Mark III units provide acquisition/resource-interaction redundancy;
- a Mark V registry/telemetry/tagging support role is corroborated by Type 1 Systems Solar Hull UC-005 at design stage (registry/telemetry casing and low-power support); ownership/yield claims remain prohibited;
- a minimum John/UTP process-cell skeleton provides assay, feed preparation, printing and repair;
- secure identity/comms/metrology plus specialist seed components establish the initial trusted base;
- the node grows only through independently calibrated child modules;
- Project-C/Watchtower-style debris awareness defines the local safeguard layer;
- resource/value return remains subordinate to safety, stewardship and evidence.

This is not a flight manifest or a mission-readiness statement.

## 10. DIY, enterprise, government and nonprofit interface

PT-079 should expose the same graph at different permission levels.

**Individual / education / maker:** passive structures, benign materials, simple sensors, low-voltage identity and safe coupons.  
**Business / workshop:** calibrated process cells, material passports, traceable QA, repair/manufacturing recipes.  
**Government / infrastructure:** standards, cybersecurity, public safety, procurement, geospatial asset state, audit and lifecycle evidence.  
**Nonprofit / cleanup / ecological programme:** simple field collection and monitoring teams backed by a smaller qualified technical core, with volunteers never silently inheriting specialist permissions.

The UI should show: *what can be made here, with what, why it is allowed, what remains unknown, what test closes the next gate, and what must still be imported or escalated.*

## 11. Validation path

1. **L0** schema/arithmetic/identity checks.
2. **L1** deterministic simulation and explicit falsifiers.
3. **L2** benign material/passive bench article.
4. **L3** material/process coupon + metrology.
5. **L4** functional device/subassembly.
6. **L5** coupled multiphysics + relevant environment.
7. **L6** recursive/module interface and independent calibration.
8. **L7** macro/system integration + degraded/safe-state tests.
9. **L8** specialist high-consequence qualification.
10. **L9** site/mission/regulatory acceptance where applicable.

Raphael may propose or compare novel relations, but standard physics/engineering baselines stay explicit and Raphael output alone never promotes a physical claim.

## 12. Immediate implementation sequence

1. Keep Drive as the owning catalogue/evidence surface.
2. Use this Git mirror for typed contracts, tests and reproducible implementation only.
3. Implement a LightSpeed view joining PT/PMX/RIP records by stable ID.
4. Bind PT-071 to the current node-exchange identity/capability/lease/receipt model.
5. Add a local-horizon compiler fixture using measured inventory and hard constraints.
6. Select first low-consequence coupons: passive identity/antenna, conductive trace, simple sensor, functional coating and recovered-feed coupon.
7. Progress structural-energy work only after separate material, electrical/electrochemical and structural tests exist.
8. Keep Mark V claims beyond UC-005 registry/telemetry casing and low-power support, plus debris actuation, biological resonance and mission operations, behind explicit evidence/owner gates.
