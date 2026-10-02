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
