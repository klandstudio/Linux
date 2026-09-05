# Phanteks LCD6-HD — Research Status and Architecture Reset

**Date:** 2026-09-04

This document summarizes the current evidence boundary for the LCD6-HD Linux interoperability project and records a change in research direction. It intentionally distinguishes hardware validation, recovered-source evidence, capture evidence, and unresolved questions.

The project has successfully established both a static-image path and a native live-telemetry path. The current research reset concerns **presentation architecture**, not basic Linux device control.

---

## Evidence labels

- **Physically validated** — observed directly on LCD6-HD hardware.
- **Source-confirmed** — supported by recovered installed NexLinq/vendor software behavior.
- **Capture-confirmed** — supported by known-good USB transaction captures.
- **Inference** — architectural interpretation of confirmed facts.
- **Unknown / unresolved** — not supported strongly enough to claim.

---

## What is physically validated

### Static image path

Linux can upload and activate a 1480×720 JPEG. The applied image persists across normal shutdown and complete AC-power removal.

### Native live telemetry

Linux can configure native sensor widgets and drive them with the NexLinq-compatible telemetry path:

```text
0x30 native widget configuration
0x21 recurring 123-byte telemetry
512-byte echo acknowledgements
visible native graph/value updates
```

Multiple simultaneous native widgets are physically validated. A layoutIndex 10 run successfully displayed CPU temperature, GPU power, and a second NVMe temperature field at the same time while sharing one live telemetry stream.

The LCD retains the last native state after the sender stops, so a visible frozen value is not proof of continued telemetry delivery.

### Physically validated selector set

| ID | Metric |
|---:|---|
| 1 | CPU temperature |
| 7 | top radiator fan RPM |
| 8 | rear fan RPM |
| 9 | AIO pump RPM |
| 10 | side fan RPM |
| 11 | bottom fan RPM |
| 27 | CPU utilization |
| 28 | CPU clock |
| 30 | GPU 1 utilization |
| 31 | GPU 1 clock |
| 32 | GPU 1 power |
| 42 | RAM used |
| 46 | NVMe 0 temperature |
| 47 | NVMe 1 temperature |

Selectors `33–41` remain deliberately unresolved.

Source-specific maxima are physically validated for the relevant fan, clock, GPU-power, and RAM widgets. In particular, RTX 3090 native power maximum maps to NVIDIA `power.max_limit`, and RAM selector `42` uses the vendor's unusual packed widget maximum described in the main documentation.

### Line-widget history behavior

Physical testing is consistent with:

```text
left   = rolling minimum
middle = rolling maximum
right  = current value
```

The current value updates first while older extrema remain until they age out over approximately the visible graph-history width. Recovered NexLinq preview logic has analogous min/max/current history semantics, but this project does not claim that firmware implements the JavaScript algorithm identically.

---

## Source-confirmed Layout 9 geometry

The LCD canvas is 1480×720.

For **flipped layoutIndex 9**, recovered NexLinq layout behavior gives these six fixed pane rectangles:

| Index | Rectangle | Size |
|---:|---|---|
| 0 | x 0–369, y 360–719 | 370×360 |
| 1 | x 370–739, y 360–719 | 370×360 |
| 2 | x 740–1109, y 360–719 | 370×360 |
| 3 | x 1110–1479, y 360–719 | 370×360 |
| 4 | x 0–739, y 0–359 | 740×360 |
| 5 | x 740–1479, y 0–359 | 740×360 |

The flip setting is serialized into device configuration; it is not only a browser-preview transformation.

This proves pane geometry. It does **not** prove arbitrary internal pixel placement of native diagnostic elements.

---

## Important current limitations

### No proven arbitrary native diagnostic XYWH

Recovered native diagnostic configuration exposes source, maximum, style, alarm, label/text, mode, and a `position` concept, but the project has not found a source-confirmed general-purpose diagnostic `x`, `y`, `width`, or `height` interface.

Accordingly, this repository does not claim that stock native widgets can be freely positioned within a layout pane.

### Typography is not validated as freeform

Recent targeted research did not produce a physically validated mechanism for changing the native diagnostic typeface or freely selecting diagnostic font size. A line-graph versus bar-graph change observed during a control test was a graph-style change, not typography evidence.

### Media crop controls are not diagnostic coordinates

Recovered `mediaX` / `mediaY` behavior belongs to media crop/pan handling and should not be interpreted as native diagnostic XY placement.

### Pane rectangles are known; arbitrary writable subregions are not

The six Layout 9 pane rectangles are source-confirmed. Exact general-purpose writable/clip regions for arbitrary native text/value composition inside those panes are not established.

---

## Product capability observed but not yet reproduced from Linux

A background image and live native diagnostic content have been observed coexisting in the vendor Windows application.

The unresolved interoperability questions are narrower:

- exact sequencing/state needed to reproduce that combined mode from Linux;
- z-order and persistence rules;
- whether later media writes preserve native overlays and vice versa.

The general coexistence concept does not need to be re-proved; its Linux state model does.

---

## Media/video direction

Recovered vendor code has distinct image and video write paths. The static image path is already physically validated. Practical dynamic video/media behavior from Linux is not yet validated.

High-value unanswered questions include:

- usable dynamic frame/update cadence;
- latency and stability;
- flicker/tearing behavior;
- USB/host cost at dashboard-refresh rates;
- whether partial-region refresh exists;
- whether native overlays can coexist with repeated media/video updates.

These questions are now more architecturally important than broad font or coordinate probing.

---

## Research direction reset

The project is pausing broad attempts to make the stock native renderer behave like a freeform dashboard compositor.

**Inference:** current evidence fits a vendor-defined, fixed-pane/template renderer better than a general-purpose arbitrary-position compositor.

Future work should compare three practical architectures:

1. **Constrained native:** embrace stock native panes/templates and adapt the visual design.
2. **Software-rendered media:** render the complete dashboard on Linux and transmit it through a practical image/video path.
3. **Hybrid:** use persistent artwork/background media plus a small number of stock native overlays whose geometry is acceptable.

Any additional reverse-engineering experiment should be narrowly chosen because its result changes which of these architectures is preferred.

---

## Stop criteria for future probing

Until stronger source/capture evidence appears, the project should avoid:

- blind font-byte probing;
- arbitrary undocumented-byte fuzzing for placement;
- repeated manual XY approximation;
- treating `position`, `mediaX`, or `mediaY` as arbitrary diagnostic coordinates without proof;
- physical tests that do not answer a specific architecture decision.

A useful next experiment should state beforehand what architectural question it answers and how each possible outcome changes the implementation plan.

---

## Unresolved hardware/data scope

The public selector list remains conservative. The second RTX 3090 mapping has not been validated in this work, and selector IDs `33–41` remain unresolved.

CPU power and PSU telemetry should remain zero/unmapped until verified local telemetry sources exist rather than being fabricated.

---

## Publication boundary

This repository intentionally excludes:

- raw PCAP/PCAPNG captures;
- firmware binaries;
- vendor DLL/EXE binaries;
- extracted NexLinq resources;
- decompiled vendor source;
- device serial numbers;
- workstation-private configuration not required for reproducibility.

Only derived interoperability facts, sanitized validation records, and implementation code are published.

---

## Current strategic question

The core Linux protocol problem is substantially solved. The next question is presentation architecture:

> Which rendering path gives the best combination of visual fidelity, live telemetry quality, reliability, and development effort without requiring open-ended reverse engineering of the stock native renderer?

The next work should answer that question before returning to low-level UI probing.
