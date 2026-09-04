# Validation record

This file records physical LCD6-HD validation results separately from source-only protocol recovery.

## Static-image control — confirmed

Date: 2026-09-01

Linux used the established sequence:

```text
0x22 verify
0x2A configure
0x28 acknowledged JPEG pages
0x30 activate
```

The decisive activation change was:

```text
old: 01 30 00 01 00 00
new: 01 30 00 01 00 01
```

Physical result: the LCD immediately switched to the uploaded 1480×720 JPEG.

The working timing was later refined to approximately 120 ms between the `0x2A` ACK and first `0x28` page, and 100 ms between final `0x28` ACK and `0x30` apply.

## Static-image persistence — confirmed

Date: 2026-09-03

After successful Linux upload, the host was shut down and AC power removed for roughly 30 seconds. On cold startup the previously uploaded dashboard returned without another Linux image transfer.

Conclusion: repeated JPEG writes are not an appropriate live-telemetry mechanism.

## Native `0x21` transport — confirmed

Date: 2026-09-03

Both 56-byte and NexLinq-style 123-byte payloads were accepted. The LCD returned 512-byte acknowledgements matching the transmitted telemetry payload.

Accepted `0x21` telemetry alone does not create a visible widget.

## Native CPU widget — confirmed

Date: 2026-09-04

A capture-verified `0x30` line-style, one-second sensor-widget configuration displayed a native CPU-temperature graph. Subsequent full `0x21` reports visibly advanced it.

Stopping host updates left the last native layout/value displayed, proving that a frozen widget does not imply fresh telemetry.

## Full populated 123-byte Linux telemetry — confirmed

Date: 2026-09-04

The private Linux pipeline populates source-confirmed CPU/GPU/RAM/NVMe fields from real Linux telemetry.

Verified sources include:

- CPU utilization from `/proc/stat`;
- CPU current/max clock from cpufreq sysfs;
- NVIDIA utilization, graphics clocks, power draw, `power.max_limit`, and VRAM from `nvidia-smi`;
- RAM used/total from `/proc/meminfo`;
- NVMe temperature from hwmon.

For the RTX 3090:

```text
power.limit     = 370 W
power.max_limit = 390 W
```

NexLinq `PowerMax` maps to `power.max_limit`.

No verified local source exists for CPU power or PSU output/input/efficiency, so those fields remain zero by design.

## Selector 27 — CPU utilization

Physically validated end-to-end.

An idle sample of approximately `0.616%` encoded/displayed as `1`. A controlled 8-of-32-logical-CPU busy workload produced `26`, consistent with roughly 25 percentage points of deliberate load plus existing utilization and integer rounding.

## Selector 30 — GPU 1 utilization

Physically validated end-to-end.

A controlled off-screen `glmark2` run was repeated with the exact outgoing telemetry sample instrumented:

```text
GPU0 util sample: 71.0%
```

The LCD displayed `71`.

## Selector 46 — NVMe 1 temperature

Physically validated.

```text
NVMe source: 45.85 °C
encoded byte: 46
LCD: 46
```

Changing only the `0x30` selector exposed the already-retained NVMe value without an immediate new `0x21` send.

## Selector 31 — GPU 1 clock

Physically validated with source-specific maximum `2115 MHz`.

After configuring selector `31`, the LCD initially exposed a retained value near `1.93 GHz`. A fresh full telemetry packet contained `210 MHz`.

Physical footer behavior:

```text
right/current -> 210 first
left/minimum  -> 210 shortly afterward
middle/max    -> retained ~1.93 GHz until old history aged out
```

This established the footer ordering as minimum / maximum / current.

## RAM selector-42 maximum — authoritative vendor-code check

Date: 2026-09-04

The original installed `LibPhanteks.dll` was inspected directly with ILSpy rather than relying only on decompiled C#.

For LCD6-HD, LCD7-HD, and LCD10-HD, all three selector-42 source branches contain a literal decimal `86` / hex `0x56` in `getMaxValue()`:

```text
max = (whole_GiB << 8) | 0x56
```

This is therefore real vendor behavior, not a decompiler artifact.

On the validation host:

```text
RAM total:             60.341373444 GiB
0x21 RAM-total bytes:  3c 22
0x30 selector-42 max:  3c 56
```

The low-byte difference is intentional: normal telemetry uses the real hundredths (`0x22` = 34), while the widget maximum uses literal `0x56`.

## Selector 42 — RAM used

Physically validated end-to-end using maximum `0x3c56`.

The selector switch immediately exposed a retained RAM-used value of about `3.34 GiB`.

After a fresh full telemetry send, the LCD showed approximately `3.47 GiB`:

- right/current changed first;
- middle/maximum followed because the new sample exceeded the retained value;
- left/minimum retained `3.34` while that old sample remained in history.

Conclusion: selector `42` and the vendor-specific maximum rule are physically validated.

## Selector 28 — CPU clock

Physically validated end-to-end using source-specific maximum `5756 MHz`.

Before the fresh send, selector `28` exposed a retained `624 MHz` sample.

The exact outgoing sample was:

```text
CPU clock sample: 4373.353 MHz
```

The LCD displayed:

```text
right/current: 4.37 GHz
middle/max:    4.37 GHz
left/min:      624 MHz retained initially
```

The old `624` minimum did not disappear merely after a short fixed delay. It aged out only when the graph had advanced across the entire visible plotting width.

Conclusion: selector `28` is physically validated, and the history-window observation was strengthened.

## Selector 32 — GPU 1 power

Physically validated end-to-end using source-specific maximum `390 W`.

Immediately after selecting source `32`, the display filled from zero to an idle value around `10`.

The exact outgoing sample from the validating send was:

```text
GPU0 power sample: 9.46 W
```

The packet's u16 rounding produced `9`, and the LCD behaved as follows:

- right/current changed immediately to `9 W`;
- left/minimum followed about 0.5 seconds later;
- middle/maximum retained the previous `10` for the full visible graph-history width;
- once the old sample aged out, all three numeric values were `9`.

Only the right/current footer value displayed the `W` unit suffix; left/minimum and middle/maximum were unitless.

Conclusion: selector `32` and `PowerMax = power.max_limit = 390 W` are physically validated.

## Selectors 7-11 — first physical fan batch

Date: 2026-09-04

The first five fan slots populated by the Linux `0x21` packet were tested individually as native line widgets. Each widget used the vendor-valid configured maximum:

```text
max_value = 4000 RPM
0x30 max bytes = 0f a0 0f a0 0f a0
```

The observed LCD transition for each selector was `0 -> value`, after which all three footer values matched because only the fresh sample was present in the new graph history:

| Selector | Mapped source | LCD result |
|---:|---|---:|
| 7 | top radiator fans | `0 -> 717 x3` |
| 8 | rear fans | `0 -> 693 x3` |
| 9 | AIO pump | `0 -> 3125 x3` |
| 10 | side fans | `0 -> 539 x3` |
| 11 | bottom fans | `0 -> 498 x3` |

The ordering and characteristic RPM ranges match the established first-five fan-slot mapping in the full Linux packet, with selector `9` especially distinguished by the ~3100 RPM pump speed.

Conclusion: selectors `7-11` are physically validated as the workstation's top, rear, pump, side, and bottom RPM sources. The public builder therefore allowlists these five selectors and requires a nonzero source-specific maximum for them.

GPU fan percentage from `nvidia-smi` remains excluded because percentage is not physical tachometer RPM.

## Line-widget history semantics — refined physical result

Across GPU clock, RAM used, CPU clock, and GPU power testing, the footer behaves as:

```text
left   = minimum of rolling visible history
middle = maximum of rolling visible history
right  = current value
```

Current updates first. History-derived extrema persist until the old sample leaves the visible rolling history. Physical observation now strongly ties the retention interval to the graph's visible plotting width rather than an arbitrary independent timer.

This is consistent with recovered NexLinq preview logic, but no claim is made that firmware internally executes the exact JavaScript algorithm.

## Current boundary

### Physically validated native selectors

```text
1   CPU temperature
7   top radiator fan RPM
8   rear fan RPM
9   AIO pump RPM
10  side fan RPM
11  bottom fan RPM
27  CPU utilization
28  CPU clock
30  GPU 1 utilization
31  GPU 1 clock
32  GPU 1 power
42  RAM used
46  NVMe 1 temperature
```

### Source-confirmed but not yet physically exercised as separate widgets

- fan selectors `12-26`, only when actual mapped RPM sources exist;
- additional NVMe/SATA selectors `47-55`;
- PSU selectors `43-45` (local live telemetry unavailable).

### Intentionally unresolved / unavailable

- selector IDs `33-41`;
- live CPU power selector `29` until a verified Linux source exists;
- live PSU output/input/efficiency on the validation host;
- GPU fan percentage as a substitute for physical RPM;
- multiple simultaneous native widgets;
- generalized placement/color/alarm behavior;
- second RTX 3090 native-widget behavior.

## Next validation targets

With selectors `7-11` complete, next work is limited to sources for which real telemetry exists:

- additional NVMe/SATA selectors;
- remaining fan selectors only when a genuine mapped tachometer RPM source is available;
- automatic selector-to-max derivation;
- `native-live` support for max-dependent selectors.

CPU power selector `29` and PSU selectors `43-45` remain out of live testing until verified local telemetry sources exist.
