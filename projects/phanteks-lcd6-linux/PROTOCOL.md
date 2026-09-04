# Phanteks LCD6-HD protocol notes

These notes describe behavior observed from Phanteks NexLinq traffic, recovered from installed NexLinq code/resources, and validated against a real LCD6-HD. They are not an official Phanteks specification.

## USB identity

- VID:PID: `1f3a:6502`
- HID report ID: `0x01`
- HID OUT report size: 1024 bytes
- HID IN report size: 512 bytes
- HID usage page observed: `0xff1b`
- HID usage observed: `0x91`

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

Working static-image activation begins:

```text
01 30 00 01 00 01 ...
```

An earlier failed reconstruction used:

```text
01 30 00 01 00 00 ...
```

For native sensor widgets, report offset 11 is widget type `0x02`.

Validated graph styles:

```text
0x03 = line
0x02 = bar
```

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

| Widget payload | Report | Meaning |
|---:|---:|---|
| 0 | 11 | widget type `0x02` |
| 1 | 12 | widget mode/style |
| 2 | 13 | position |
| 3-5 | 14-16 | source selectors 1-3 |
| 6-11 | 17-22 | three u16 BE source-specific maxima |
| 12-13 | 23-24 | alarm temperature/RPM |
| 14 | 25 | alarm enable where applicable |
| 15 | 26 | frequency |
| 16 | 27 | text1 length |
| 17-48 | 28-59 | text1 |
| 49 | 60 | text2 length |
| 50-81 | 61-92 | text2 |
| 82 | 93 | text3 length |
| 83-114 | 94-125 | text3 |

### Source-specific maximum values

Installed vendor code confirms:

```text
fan 7-26 -> configured max RPM
28       -> CPU ClockMax
29       -> CPU PowerMax
31       -> GPU 1 ClockMax
32       -> GPU 1 PowerMax
42       -> packed RAM total
43-44    -> constant 1200 display scale
```

Physically validated examples:

```text
28 CPU clock: 5756 MHz
31 GPU clock: 2115 MHz
32 GPU power: 390 W
42 RAM used:  0x3c56 on 60.34 GiB OS-visible RAM
```

### RAM selector 42 maximum

The selector-42 maximum is intentionally unusual.

Direct IL inspection of the installed vendor `LibPhanteks.dll` showed that LCD6-HD, LCD7-HD, and LCD10-HD all use the same rule in `getMaxValue()` for source `42` and for all three source slots:

```text
whole = getRamGB(hwRam.TotalSize)[0]
max = (whole << 8) | 0x56
```

The low byte is a literal `0x56` / decimal `86`; it is not `getRamGB(...)[1]` and is not a decompiler artifact.

On the validation host:

```text
RAM total:             60.34 GiB
0x21 RAM-total bytes:  3c 22
0x30 selector-42 max:  3c 56
```

So the normal telemetry path uses the real whole/hundredths bytes, while the widget maximum uses the vendor-specific literal low byte.

## Recovered source selectors

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
| 33-41 | GPU-associated internally, not assigned/exposed by recovered NexLinq UI |
| 42 | RAM used |
| 43 | PSU Power Out |
| 44 | PSU Power In |
| 45 | PSU Efficiency |
| 46-50 | NVMe temperatures |
| 51-55 | SATA temperatures |

IDs `33-41` remain intentionally unresolved.

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
| 113-117 | 5× u8 | NVMe temperatures |
| 118-122 | 5× u8 | SATA temperatures |

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

RAM telemetry is encoded as one byte for whole GiB plus one byte for the two-digit decimal portion.

## Physically validated native selectors

| Selector | Metric | Physical result |
|---:|---|---|
| 1 | CPU temperature | native line widget and live graph confirmed |
| 27 | CPU utilization | controlled load and integer rounding confirmed |
| 28 | CPU clock | 4373.353 MHz same sample displayed as 4.37 GHz |
| 30 | GPU 1 utilization | exact same-sample 71% collector/display correlation |
| 31 | GPU 1 clock | retained ~1.93 GHz -> fresh 210 MHz with 2115 MHz maximum |
| 32 | GPU 1 power | 9.46 W sample encoded/displayed as 9 W with 390 W maximum |
| 42 | RAM used | retained 3.34 GiB -> fresh ~3.47 GiB using `0x3c56` max |
| 46 | NVMe 1 temperature | 45.85 °C encoded/displayed as 46 °C |

## Line-widget footer/history semantics

Physical testing establishes:

```text
left   = minimum of rolling visible history
middle = maximum of rolling visible history
right  = current value
```

Current updates first. Old min/max samples remain until they age out of the rolling graph history. During CPU-clock and GPU-power testing, the old history value disappeared only after the graph had advanced across the full visible plotting width.

This agrees with recovered NexLinq preview logic that maintains a rolling data array and derives min/max/current separately. The firmware's internal algorithm is not claimed to be byte-for-byte identical to the JavaScript preview.

For selector `32`, only the right/current footer value displayed the `W` suffix; left/minimum and middle/maximum were unitless.

## Linux full-payload sources

Verified Linux sources include:

- CPU utilization from `/proc/stat`;
- CPU current/max clock from `cpufreq` sysfs;
- NVIDIA current/max graphics clock from `nvidia-smi`;
- NVIDIA current power draw;
- NVIDIA `power.max_limit` for NexLinq `PowerMax`;
- NVIDIA used/total VRAM;
- RAM used/total from `/proc/meminfo`;
- NVMe temperature from hwmon.

For the RTX 3090:

```text
power.limit     370 W
power.max_limit 390 W
```

`PowerMax` maps to `power.max_limit`.

No verified Linux CPU-power or PSU telemetry source is present on the validation machine. Those payload fields remain zero by design.

## Fan-selector boundary

Selectors `7-26` are source-confirmed as fan RPM inputs. The NexLinq LCD6-HD UI permits configured fan maxima from `500` to `4000` RPM in `100` RPM steps, default `2000`.

The next physical batch is selectors `7-11`, corresponding in the current Linux packet to top, rear, pump, side, and bottom RPM values. GPU fan percentage from `nvidia-smi` is not treated as physical RPM and is not mapped into these slots.

## Publication boundary

This project does not redistribute firmware, vendor binaries, decompiled source, extracted vendor UI assets, serial numbers, or raw validation captures. Only derived interoperability facts and cleaned validated code are published.
