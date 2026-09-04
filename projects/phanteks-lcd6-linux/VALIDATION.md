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

CPU current clock is dynamic and changes normally between samples.

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

### Offline packet inspection

Before sending, Linux built and decoded the 123-byte packet entirely in memory.

Representative result:

```text
payload_len: 123
cpu_temp: 37
cpu_util: 0
cpu_clock_mhz: 4386
cpu_power_w: 0
ram_used: 3.26 GiB
psu_out_w: 0
psu_in_w: 0
psu_eff_pct: 0
ram_total: 60.34 GiB
cpu_clock_max_mhz: 5756
cpu_power_max_w: 0
gpu0: util=0%
      clock=210MHz
      power=9W
      vram_used=15MiB
      clock_max=2115MHz
      power_max=390W
      vram_total=24576MiB
nvme0_temp: 47
```

The one-shot offline test showed CPU utilization as zero because a fresh sampler had not yet accumulated its second `/proc/stat` sample. The production send path performs the second sample before transmitting.

### Physical full-packet test

Before the command, the LCD was watched continuously.

Command:

```text
python3 -m panda_lcd.cli telemetry-send-once --full
```

Terminal result:

```text
CPU: 36.625 C
GPU temps: [33.0]
Fan RPMs [top,rear,pump,side,bottom]: [699, 774, 3116, 565, 497]
Sent one 0x21 packet (123-byte full) to /dev/hidraw4; ACK length=512
```

Physical observation from the user:

```text
graph went up by 1
```

This is the key September 4 milestone. It confirms that:

- the fully populated report is accepted;
- the 512-byte ACK matches the transmitted telemetry payload;
- the expanded fields do not disrupt native telemetry;
- the active native CPU graph consumes the report and advances visibly.

The full populated 123-byte Linux telemetry implementation is therefore **physically validated**.

## Code-quality checkpoint — passed

The modified private files were diff-reviewed:

```text
panda_lcd/telemetry.py
panda_lcd/phanteks.py
panda_lcd/cli.py
```

Only intended changes were observed.

Syntax validation passed:

```text
python3 -m py_compile panda_lcd/phanteks.py panda_lcd/telemetry.py panda_lcd/cli.py
```

The stale telemetry-builder docstring was corrected and a duplicate local u8 helper was removed.

## Current boundary

### Physically validated

- static JPEG upload and activation from Linux;
- static image retention across complete AC power loss;
- 56-byte `0x21` transport;
- 123-byte `0x21` transport;
- native CPU-temperature `0x30` widget;
- thirty-cycle native live graph updates;
- retained-last-value behavior after host updates stop;
- **populated** 123-byte CPU/GPU/RAM/NVMe Linux telemetry;
- 512-byte ACK validation of the expanded payload;
- visible graph advancement using the expanded payload.

### Source-confirmed but not yet physically exercised as separate native widgets

- CPU utilization selector `27`;
- CPU clock selector `28`;
- GPU load/clock/power selectors `30-32`;
- RAM selector `42`;
- PSU selectors `43-45`;
- NVMe/SATA selectors `46-55`.

### Intentionally unresolved / unavailable

- selector IDs `33-41`;
- live CPU power on the validation host;
- live PSU output/input/efficiency on the validation host;
- multiple simultaneous native widgets;
- generalized placement/color/alarm behavior;
- second RTX 3090 native-widget behavior.

## Next validation target

Generalize the private `0x30` sensor-widget builder to an allowlisted, already recovered source selector. Build/decode candidate reports offline first, then physically test one low-risk source such as CPU utilization (`27`) or GPU load (`30`). Arbitrary selector probing remains out of scope.
