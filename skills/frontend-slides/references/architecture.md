# Architecture

`frontend-slides` now has two layers:

1. **Runtime layer**: `assets/runtime/` contains hash-locked browser runtime files. Generated decks load the stage component.
2. **Skill layer**: prompt instructions, style references, flattened template metadata, and runnable template shells.

## Runtime Layer

The generated HTML renders slides as direct `section` children of `deck-stage`, and the stage component owns:

- fixed 1920×1080 stage sizing;
- viewport scaling and letterboxing;
- keyboard navigation;
- touch tap zones;
- slide count and reset overlay;
- print layout.

The hash lock in `assets/runtime-manifest.json` protects the runtime files.

## Skill Layer

The migrated skill inherits `frontend-slides` generation guidance:

- style discovery with curated presets;
- compact template selection index at `templates/selection-index.json`;
- flattened template shells and design notes;
- shared deck-stage runtime behavior.

Unlike upstream `frontend-slides`, the default generated decks are flattened template shells that load only `assets/runtime/deck-stage.js`. Fixed-stage references live beside them in `templates/<slug>/design.md`.
