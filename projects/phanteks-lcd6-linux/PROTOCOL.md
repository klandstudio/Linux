# Phanteks LCD6-HD protocol notes

These notes describe behavior observed from Phanteks NexLinq traffic, recovered from installed NexLinq code/resources, and validated against a real LCD6-HD. They are not an official Phanteks specification.

## USB identity

- VID:PID: `1f3a:6502`
- HID report ID: `0x01`
- HID OUT report size: 1024 bytes
- HID IN report size: 512 bytes
- HID usage page observed: `0xff1b`
- HID usage observed: `0x91`

The confirmed static-image and native telemetry paths use HID.

## Confirmed commands

### `0x22` — device information

A 1024-byte OUT report with report ID `0x01`, command `0x22`, and remaining bytes zero returns a 512-byte IN report. Payload begins at report offset 11.

Observed firmware strings include:

```text
W2,1A18C,AIO,FDT,LCD6-HD,V1.0.0.0,Dec 16 2025,14:57:39
W2,1A18C,AIO,FDT,LCD6-HD,V1.0.0.10,Aug  6 2026,13:53:58
```

### `0x2A` — LCD configuration / prepare

Validated Linux static-image configuration:

| Offset | Meaning | Value |
|---:|---|---|
| 0 | report ID | `0x01` |
| 1 | command | `0x2A` |
| 9-10 | payload length | `0x0009` BE |
| 11 | layout/mode | `0x00` background-only |
| 12 | brightness | 0-100 |
| 13 | orientation | `0x00` landscape |
| 14 | background mode | `0x00` image |
| 15 | flags | `0x00` |
| 16-19 | ARGB fallback | `ff 00 00 00` |

The device returns the expected 512-byte response. The working Linux sequence waits about 120 ms before the first JPEG packet.

### `0x28` — JPEG transfer

| Offset | Meaning |
|---:|---|
| 0 | report ID `0x01` |
| 1 | command `0x28` |
| 2-5 | total JPEG length, u32 BE |
| 6-8 | zero-based page, 24-bit BE |
| 9-10 | chunk length + 1, u16 BE |
| 11 | media slot; `0xFF` = background |
| 12+ | up to 1012 JPEG bytes |

Each page is acknowledged before the next page is sent.

### `0x30` — apply / commit / widget configuration

`0x30` is used for multiple layout/configuration operations.

Working static-image activation begins:

```text
01 30 00 01 00 01 ...
```

An earlier failed reconstruction used:

```text
01 30 00 01 00 00 ...
```

For native sensor widgets, the request state at report offset 11 is `0x02`.

Validated graph styles:

```text
0x03 = line
0x02 = bar
```

Validated private Linux implementation currently permits widget intervals of 1 or 10 seconds. NexLinq UI/source also contains other frequency values, but they are not exposed by the cleaned public builder until directly validated.

## Source-confirmed `0x30` sensor-widget structure

NexLinq `SetLcdInfo` builds this common report header:

| Report offset | Meaning |
|---:|---|
| 0 | report ID `0x01` |
| 1 | command `0x30` |
| 3 | total LCD items |
| 4 | item index |
| 5 | layout index |
| 6-8 | zero-based item iteration, 24-bit BE |
| 11+ | widget payload |

For sensor widget type `0x02`:

| Widget payload offset | Report offset | Meaning |
|---:|---:|---|
| 0 | 11 | widget type `0x02` |
| 1 | 12 | widget mode/style |
| 2 | 13 | position |
| 3-5 | 14-16 | source selectors 1-3 |
| 6-11 | 17-22 | three u16 BE maximum values |
| 12-13 | 23-24 | alarm temperature/RPM |
| 14 | 25 | alarm enable where applicable |
| 15 | 26 | frequency |
| 16 | 27 | text1 length |
| 17-48 | 28-59 | text1, max 32 bytes |
| 49 | 60 | text2 length |
| 50-81 | 61-92 | text2 |
| 82 | 93 | text3 length |
| 83-114 | 94-125 | text3 |
| 125-148 | 136-159 | colors 1-6, ARGB |
| 165+ | 176+ | mode-derived bright colors |

The physically validated CPU-temperature line/1-second request starts:

```text
01 30 00 01 00 01 00 00 00 00 00
02 03 02 01 01 01 ...
```

with label `AMD Ryzen 9 9950X`.

## Recovered source selectors

The embedded NexLinq WebView resources were extracted from the installed executable and inspected offline. Menu construction plus `getSourceValue()` / `getSourceName()` establish:

| ID | Meaning / status |
|---:|---|
| 1 | CPU temperature |
| 2-6 | GPU temperature source class |
| 7-26 | fan RPM 1-20 |
| 27 | CPU utilization |
| 28 | CPU clock |
| 29 | CPU power |
| 30 | GPU 1 load |
| 31 | GPU 1 clock speed |
| 32 | GPU 1 power |
| 33-41 | GPU-associated internally, but not assigned/exposed by the recovered NexLinq UI |
| 42 | RAM used |
| 43 | PSU Power Out |
| 44 | PSU Power In |
| 45 | PSU Efficiency |
| 46-50 | NVMe temperatures |
| 51-55 | SATA temperatures |

The recovered menu currently creates first-GPU entries for selector `2`, `30`, `31`, and `32`.

IDs `33-41` were searched across all extracted NexLinq JavaScript. No selector menu entry, parameter, or source assignment was found. Decompiled C# `getMaxValue()` also provides no selector-specific handling for them. They remain intentionally unresolved.

`getMaxValue()` confirms mode-specific maxima for:

- fan selectors `7-26` -> configured max RPM;
- `28` -> CPU max clock;
- `29` -> CPU max power;
- `31` -> GPU 1 max clock;
- `32` -> GPU 1 max power;
- `42` -> packed RAM total;
- `43-44` -> constant display scale `1200`.

The `1200` PSU scale is not evidence that live PSU telemetry exists on a particular host.

## `0x21` — SetHandshakeData telemetry

NexLinq normally sends a 123-byte payload. Payload begins at report offset 11 and report offsets 9-10 contain the payload length.

| Payload offset | Encoding | Meaning |
|---:|---|---|
| 0-3 | u32 BE | timestamp |
| 4 | u8 | UTC/state |
| 10 | u8 | CPU temperature |
| 11-15 | 5× u8 | GPU temperatures 0-4 |
| 16-55 | 20× u16 BE | fan RPMs 0-19 |
| 56 | u8 | CPU utilization |
| 57-58 | u16 BE | CPU current clock |
| 59-60 | u16 BE | CPU power |
| 61-81 | 5× 7-byte groups | GPU usage, clock, power, used VRAM |
| 82-83 | whole + hundredths bytes | RAM used GiB |
| 84-85 | u16 BE | PSU output power |
| 86-87 | u16 BE | PSU input power |
| 88 | u8 | PSU efficiency |
| 89-90 | whole + hundredths bytes | RAM total GiB |
| 91-92 | u16 BE | CPU maximum clock |
| 93-94 | u16 BE | CPU maximum power |
| 95-112 | 5× 6-byte groups | GPU max clock, max power, total VRAM |
| 113-117 | 5× u8 | deduplicated NVMe temperatures |
| 118-122 | 5× u8 | deduplicated SATA temperatures |

Current GPU group at `61 + i*7`:

```text
+0 usage u8
+1..2 clock u16 BE
+3..4 power u16 BE
+5..6 used VRAM u16 BE
```

Maximum GPU group at `95 + i*6`:

```text
+0..1 max clock u16 BE
+2..3 max power u16 BE
+4..5 total VRAM u16 BE
```

NexLinq rounds GPU numeric values before u16 encoding.

RAM is encoded as one byte for whole GiB plus one byte for the two-digit decimal portion.

## Linux full-payload population — physically validated

On September 4, 2026 Linux populated the source-confirmed trailing fields with real telemetry instead of leaving offsets 56-122 zero.

Verified Linux sources include:

- CPU utilization from `/proc/stat`;
- CPU current/max clock from `cpufreq` sysfs;
- NVIDIA current/max graphics clock from `nvidia-smi`;
- NVIDIA current power draw;
- NVIDIA `power.max_limit` for NexLinq `PowerMax`;
- NVIDIA used/total VRAM;
- RAM used/total from `/proc/meminfo`;
- NVMe temperature from hwmon.

A representative RTX 3090 reported:

```text
current clock 210 MHz
max clock     2115 MHz
power draw    about 9-10 W idle
power.limit   370 W
power.max_limit 390 W
VRAM          15 / 24576 MiB
```

`PowerMax` maps to `power.max_limit` (390 W in this test), not the current software `power.limit` (370 W).

No verified Linux CPU-power or PSU telemetry source was present on the validation machine. Therefore these fields remain zero by design:

```text
59-60 CPU power
84-85 PSU output
86-87 PSU input
88    PSU efficiency
93-94 CPU max power
```

The expanded 123-byte packet received a matching 512-byte acknowledgement and the existing native CPU graph visibly advanced by one sample.

## Confirmed static sequence

```text
open HID session
 -> 0x22 verify
 -> 0x2A configure
 -> wait ~120 ms
 -> acknowledged 0x28 JPEG pages
 -> wait ~100 ms
 -> 0x30 apply with 01 30 00 01 00 01 ...
 -> require success response
close session
```

## Persistence finding

The static JPEG survives complete power loss. Live telemetry should therefore use native `0x21` reports plus native `0x30` widget configuration, not repeated JPEG uploads.

Native widgets also retain the last layout/value after host updates stop. A frozen visible graph is not proof that fresh telemetry is arriving.

## Publication boundary

This project does not redistribute firmware, vendor binaries, decompiled source, extracted vendor UI assets, serial numbers, or raw validation captures. Only derived interoperability facts and cleaned validated code are published.
