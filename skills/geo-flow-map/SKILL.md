---
name: "geo-flow-map"
description: "Generates zero-dependency interactive SVG geographic maps from user intent, including real-outline world and China maps, markers, regions, flow routes, labels, tooltips, and map-scope inference."
---

# Geo Flow Map

Use this skill when the user asks for a geographic SVG map, world map, China
map, migration/trade/war/diffusion route map, location annotation map, regional
outline map, or an interactive map-based visual explanation.

Before producing a map, read `references/harness.md` for the workflow, data contracts,
validation checklist, and delivery rules. The reference implementation is
`assets/template.html`; architecture and data contracts are documented under
`references/`.

## Workflow Overview

Use this checkpointed workflow when the skill output is a publishable article-style artifact. Keep checkpoints explicit and stop at each checkpoint until the user confirms the listed decisions.

```
Phase 0  Intake
         Decide whether this skill applies and identify the initial article type.
  🔽
Phase 1  Source -> Markdown
         Convert URL/PDF/DOCX/MD/text into source.md + extraction-notes.md.
         The main agent runs a 5-item inline checklist; only complex or low-confidence sources escalate to a SubAgent.
  🔽
Phase 2  Editorial Planning
         Create one plan.md with four sections: Brief / Outline / Theme / Assets.
         The main agent self-checks inline; no SubAgent and no review file.
  🔽
Phase 3  Plan Checkpoint
         Checkpoint 1 must stop. Confirm five items one by one:
         article type with standard retention ratio / theme / layout / image mode / cover.
  🔽
Phase 4  First Spread
         Build the hero, first section, and one representative visual block. Create the scaffold here.
         First Spread Reviewer SubAgent writes review/first-spread-review.md.
         Checkpoint 2 must stop. Confirm two items one by one:
         acceptance result / development mode A or B.
  🔽
Phase 5  Full Article Build
         Generate the complete web article. Default to one agent; isolate by section only for very long articles.
         Section Reviewer SubAgent returns pass/fail in the message and does not write a review file.
  🔽
Phase 6  Final Review
         Run Editorial / Visual / Technical final review and write review/final-review.md.
  🔽
Phase 7  Repair
         Apply minimal-slice repairs. Write repair-log.md only when repairs are made.
  🔽
Phase 8  Delivery
         Checkpoint 3 must stop. Confirm the delivery decision one by one.
         Deliver article.html plus a short editorial note.
```


## Core Requirements

1. Produce a pure native, single-file, zero-dependency HTML page whose main
   artifact is an inline SVG map.
2. Convert user intent into declarative map scenes: base map scope, geographic
   context, nodes, regions, routes, flows, labels, legends, and interactions.
3. Use real SVG map outlines for both world and China views. Do not use
   abstract rectangles, placeholder maps, raster screenshots, external images,
   CDNs, framework imports, or fetch calls.
4. Select map scope deliberately: global/cross-border subjects use `world`;
   China-local subjects use `china`; ambiguous subjects use `auto` with real
   coordinates so the renderer can infer the scope.
5. Preserve geographic semantics. Regions may include land and sea; do not clip
   region outlines to land only. Countries/regions and oceans/seas/straits must
   be named through `geoContext`, labels, or legends.
6. Keep template data map-specific. Remove unrelated narrative, glossary,
   bibliography, demo chronology, or domain content unless it directly controls
   map drawing, labels, routes, regions, risk notices, or interactions.
7. Draw China territory as one combined land-and-sea geographic expression when
   the subject involves China. Do not split land territory and maritime extent
   into competing standalone maps.
8. Use restrained cartography: thin, soft but legible strokes; China labels may
   be emphasized, while other country names should be smaller, lighter, and
   positioned to avoid crossing unrelated countries.
9. Add a lower-left detail inset when small islands, straits, coastline
   fragments, or disputed/sensitive areas cannot be read clearly on the main map.
10. Add an explicit risk notice on the map when boundaries, maritime areas,
   sovereignty, disputes, or sensitive regions are involved; state that the map
   is a visualization and official standard maps/legal documents prevail.
11. Draw intent-driven map behavior: point markers, labels, region outlines,
   route/flow polylines, arrow direction, animated drawing, hover/click
   tooltips, legend filtering, and map modal/zoom behavior when appropriate.
12. Validate SVG syntax, JavaScript syntax, map-scope inference, coordinate
   ranges, route continuity, interaction behavior, responsive layout, and
   absence of unreplaced placeholders before delivery.
13. Format the generated HTML before delivery. Treat indentation as tab-based
    structure with an indent width of 2 spaces for nested HTML, SVG, CSS, and
    JavaScript blocks.
