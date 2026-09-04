# Validation record

This file records physical LCD6-HD validation results separately from source-only protocol recovery.

## Static-image control — confirmed

Date: 2026-09-01

Firmware:

```text
V1.0.0.10
```

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

Later capture correlation refined the working timing to approximately:

- 120 ms between `0x2A` ACK and first `0x28` page;
- 100 ms between final `0x28` ACK and `0x30` apply.

The `0x30` response is checked for the observed success state.

## Static-image persistence — confirmed

Date: 2026-09-03

After a successful Linux dashboard upload, the host was shut down and AC power removed for roughly 30 seconds.

On cold startup the previously uploaded Panda dashboard returned without another Linux image transfer.

Observed sequence:

```text
Panda dashboard -> brief Phanteks screen -> Panda dashboard
```

Conclusion: repeated JPEG writes are not an appropriate live-telemetry mechanism.

## Native `0x21` transport — confirmed

Date: 2026-09-03

### 56-byte form

Linux sent live CPU/GPU/fan values in a 56-byte payload. The LCD returned a 512-byte acknowledgement whose telemetry payload matched the transmitted payload.

### Initial 123-byte form

Linux reproduced NexLinq's normal 123-byte packet shape while zero-filling the then-unresolved trailing fields.

Representative run:

```text
CPU: 35.75 C
GPU temps: [33.0]
Fan RPMs [top,rear,pump,side,bottom]: [677, 698, 3116, 554, 497]
Sent one 0x21 packet (123-byte full) to /dev/hidraw4; ACK length=512
```

Physical result while a static background-only layout was active: no visible change.

Conclusion: accepted `0x21` telemetry does not create a visible widget by itself.

## Native CPU widget — confirmed

Date: 2026-09-04

Linux reproduced a capture-verified `0x30` sensor-widget configuration using line style and one-second interval.

```text
Sent one native widget 0x30 configuration to /dev/hidraw4;
style=line, interval=1s, ACK length=512
```

Physical result: the LCD displayed a native CPU-temperature line graph labeled `AMD Ryzen 9 9950X`.

A subsequent full `0x21` report visibly changed the graph.

A `native-live` test then configured the widget once and sent one 123-byte `0x21` report per second for thirty cycles. Each observed report received a 512-byte ACK and the graph visibly advanced several times.

Ctrl+C stopped host updates cleanly. The graph remained displayed afterward, confirming that the LCD retains its last native layout/value.

## Offline selector/schema recovery — source-confirmed

Date: 2026-09-04

Installed NexLinq assemblies and embedded WebView resources were inspected from a read-only Windows mount.

Recovered source selectors include:

```text
1      CPU temperature
2-6    GPU temperature source class
7-26   fan RPM
27     CPU utilization
28     CPU clock
29     CPU power
30     GPU 1 load
31     GPU 1 clock
32     GPU 1 power
42     RAM used
43     PSU Power Out
44     PSU Power In
45     PSU Efficiency
46-50  NVMe temperature
51-55  SATA temperature
```

IDs `33-41` are GPU-associated by broad internal checks but are not assigned or exposed by the recovered NexLinq JavaScript UI. They remain intentionally unresolved.

The complete 123-byte `0x21` field layout was also source-confirmed.

## Full populated 123-byte Linux telemetry — confirmed

Date: 2026-09-04

The private Linux pipeline was extended to populate the source-confirmed trailing fields from real Linux telemetry rather than leaving offsets `56-122` zero.

### Linux data sources verified

CPU:

```text
/proc/stat                         utilization
cpu0/cpufreq/scaling_cur_freq    current clock
cpu0/cpufreq/cpuinfo_max_freq    maximum clock
```

NVIDIA query fields added:

```text
clocks.current.graphics
clocks.max.graphics
power.draw
power.limit
power.max_limit
memory.used
memory.total
utilization.gpu
```

Important distinction verified on the RTX 3090:

```text
power.limit     = 370 W
power.max_limit = 390 W
```

NexLinq `PowerMax` is populated from `power.max_limit`, not `power.limit`.

Representative telemetry after collector changes:

```text
CPU clock MHz: 4396.169
CPU max MHz:   5756.452
GPU 0: clock=210.0 MHz,
       clock_max=2115.0 MHz,
       power=9.33 W,
       power_limit=370.0 W,
       power_max=390.0 W,
       VRAM=15.0/24576.0 MiB,
       util=0.0%
```

### Unsupported fields intentionally zero

No verified Linux source was found for:

```text
CPU current power
CPU maximum power
PSU output power
PSU input power
PSU efficiency
```

Those payload fields remain zero by design.

### Physical full-packet test

Before the command, the LCD was watched continuously.

```text
CPU: 36.625 C
GPU temps: [33.0]
Fan RPMs [top,rear,pump,side,bottom]: [699, 774, 3116, 565, 497]
Sent one 0x21 packet (123-byte full) to /dev/hidraw4; ACK length=512
```

Physical observation:

```text
graph went up by 1
```

This confirms that the fully populated report is accepted, the 512-byte ACK matches the transmitted telemetry payload, and the active native widget consumes the expanded packet.

## Generalized native selector validation — confirmed

Date: 2026-09-04

The private `0x30` builder was generalized conservatively from the original hard-coded CPU-temperature source. Candidate packets were built and compared offline before every first send. Arbitrary selector probing was not used.

### Selector 27 — CPU utilization

The candidate report differed from the known-good CPU-temperature report only at report bytes `14-16`, changing source selectors from `1/1/1` to `27/27/27`.

The selector configuration received a 512-byte ACK and the graph reset to the bottom. An offline telemetry check then measured:

```text
collector CPU util: 0.6157635467980316
0x21 CPU-util byte: 1
```

The LCD plotted `1`, matching the NexLinq-compatible integer encoding.

For a controlled load test, 8 busy workers were launched on a 32-logical-CPU system. This was designed to add about 25 percentage points of total CPU utilization. The LCD displayed `26`, consistent with the deliberate ~25-point load plus the existing fractional utilization and integer rounding. The extra point should not be dismissed as arbitrary background noise.

Conclusion: selector `27` is physically validated end-to-end.

### Selector 30 — GPU 1 utilization

At idle, the Linux collector and packet both reported `0`, matching the LCD's zero trace.

A controlled off-screen `glmark2` workload was then rendered on the RTX 3090. An initial independent `nvidia-smi` sample showed 70%, while the LCD later displayed 71%. A repeat test instrumented the exact telemetry collector used for the outgoing packet:

```text
GPU0 util sample: 71.0%
Sent one 0x21 packet (123-byte full) ... ACK length=512
```

The LCD displayed `71`. This resolves the earlier 70/71 observation as sampling at different instants, not a scaling discrepancy.

Conclusion: selector `30` is physically validated end-to-end, including exact same-sample correlation.

### Selector 46 — NVMe 1 temperature

Offline measurement before selector switching:

```text
NVMe temp: 45.85
transmitted NVMe byte: 46
```

The live `0x30` selector change was accepted with a 512-byte ACK. The LCD visibly went from `0` to `46` without a new `0x21` send immediately afterward, exposing the already-retained NVMe field from the most recent full telemetry packet.

Conclusion: selector `46` is physically validated at 46 °C from a measured 45.85 °C source value.

### Source-specific maxima recovered

Decompiled `Lcd6hdMaster.getMaxValue()` confirms that report bytes `17-22` hold three u16 BE source-specific maxima. The mappings include:

```text
fan 7-26 -> configured max RPM
28       -> CPU ClockMax
29       -> CPU PowerMax
31       -> GPU 1 ClockMax
32       -> GPU 1 PowerMax
42       -> packed RAM total
43-44    -> 1200 display scale
```

### Selector 31 — GPU 1 clock

The private builder was extended to populate report bytes `17-22` with the source-specific maximum. Offline validation used the RTX 3090's recovered maximum:

```text
max1: 2115
max2: 2115
max3: 2115
GPU CLOCK 0x30 OFFLINE CHECK PASSED
```

After configuring selector `31` with maximum `2115`, the LCD immediately exposed a retained value of about `1.93 GHz`.

A fresh offline Linux sample then showed:

```text
GPU0 clock collector: 210.0 MHz
GPU0 clock packet: 210 MHz
GPU0 clock max: 2115.0 MHz
```

After one new full `0x21` send, the footer behaved differently from the earlier flat-value tests:

```text
left   -> 210 quickly
middle -> remained ~1.93 GHz for roughly 15+ seconds
right  -> 210 first/immediately
```

The middle value eventually fell to 210 as the older high sample aged out.

This physically identifies the three line-widget footer values as:

```text
left   = minimum of rolling history
middle = maximum of rolling history
right  = current value
```

The timing observation is also useful: current changed first; minimum followed extremely quickly; maximum remained until the old high sample expired from history.

Conclusion: selector `31` and its `2115 MHz` source-specific maximum are physically validated.

## Code-quality checkpoint — passed

Private files involved in this milestone:

```text
panda_lcd/telemetry.py
panda_lcd/phanteks.py
panda_lcd/cli.py
```

Syntax validation was repeatedly run with `python3 -m py_compile` after edits.

A temporary selector guard was once inserted into the wrong builder by an overly broad text replacement; the resulting `NameError` occurred before any HID send and was corrected offline. Subsequent telemetry and selector tests passed.

## Current boundary

### Physically validated

- static JPEG upload and activation from Linux;
- static image retention across complete AC power loss;
- 56-byte and 123-byte `0x21` transport;
- populated 123-byte CPU/GPU/RAM/NVMe Linux telemetry;
- 512-byte telemetry echo-ACK validation;
- native CPU-temperature selector `1`;
- CPU utilization selector `27`;
- GPU 1 utilization selector `30`;
- GPU 1 clock selector `31` with 2115 MHz maximum;
- NVMe 1 temperature selector `46`;
- retained-last-value behavior after host updates stop;
- line-widget footer semantics: min / max / current.

### Source-confirmed but not yet physically exercised as separate native widgets

- CPU clock selector `28`;
- GPU power selector `32`;
- RAM selector `42`;
- fan selectors `7-26` with configured max RPM;
- PSU selectors `43-45` (local live telemetry unavailable);
- additional NVMe/SATA selectors `47-55`.

### Intentionally unresolved / unavailable

- selector IDs `33-41`;
- live CPU power on the validation host;
- live PSU output/input/efficiency on the validation host;
- multiple simultaneous native widgets;
- generalized placement/color/alarm behavior;
- second RTX 3090 native-widget behavior.

## Next validation target

Resolve the unusual RAM-total packing used by NexLinq `getMaxValue()` for selector `42` before sending a RAM widget. Then continue with source-confirmed max-value selectors such as CPU clock `28` and GPU power `32`, always building/decoding the candidate `0x30` packet offline first.
