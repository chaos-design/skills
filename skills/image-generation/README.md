# Image Generation

[中文](./README.zh-CN.md)

Generates images from text descriptions with zero secrets. The skill never
reads, requests, or stores any API key: every image is produced through the
host environment's built-in image generation capability. Before the skill
becomes active in a session it runs a capability gate — tool discovery plus a
minimal probe generation — and refuses to operate unless the current model is
confirmed to support image output.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill image-generation
```

## What it does

| Stage | Who | Result |
| --- | --- | --- |
| Capability gate | Agent, on first invocation in a session | Step 1 discovers an image generation tool among the session's (including deferred) tools. Step 2 runs a minimal probe prompt and verifies a real image comes back — a file or a reachable URL, not text or a placeholder. Both must pass. |
| Generate | Agent | Collects the user's subject, style, composition and mood, completes the prompt per the guidance, calls the host's image generation tool, and delivers the real image. |
| Report | Agent | On any failure the skill reports which gate step failed and why, then stops. No placeholder images, no mock output, no "configure an API key" detour. |

## Design

- **The gate comes first.** The skill is not usable until the current model is
  confirmed to support image output. The gate runs once per session and re-runs
  if the model or session changes.
- **Zero secrets by construction.** There is no `.env`, no API key, no base
  URL, and no code path that could ask the user for credentials. If the host
  has no image generation capability, the correct outcome is "skill
  unavailable", never a key-based workaround.
- **No fabricated fallback.** A failed check or a failed generation is
  reported honestly. Placeholder images, ASCII art, or textual stand-ins are
  forbidden as substitutes for real output.
- **Probe artifacts are not deliverables.** The probe image proves the
  capability exists; the user's request is regenerated afterwards.

## Usage

The skill is instruction-driven; the agent follows `SKILL.md`:

1. On the first image request in a session, run the capability gate
   (tool discovery, then one minimal probe generation).
2. If the gate fails, tell the user the current model does not support image
   output and stop.
3. If the gate passes, build a complete prompt (subject, style, palette,
   composition, mood) and call the session's image generation tool.
4. Deliver the real image file or URL; reference timestamps in UTC+8,
   `YYYY-MM-DD HH:mm:ss`.

| Request parameter | Meaning | Default | Required |
| --- | --- | --- | --- |
| `prompt` | Description covering subject, style, color, composition, mood | none | yes |
| `size` | Size or aspect ratio, limited to what the host tool supports | tool default | no |
| `count` | Number of images | 1 | no |

## Requirements

- A host environment that exposes a built-in image generation tool to the
  agent (discovered through the session's tool list).
- No network credentials, no API keys, no local dependencies.

## Non-goals

- It does not call external image APIs and never accepts API keys.
- It does not edit existing images, generate video, or produce 3D models.
- It does not fake output when the capability is missing; it stops and says so.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
