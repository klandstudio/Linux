# Phanteks LCD6-HD Linux Control

Native Linux control of the **Phanteks LCD6-HD** over USB HID.

This project documents two independently validated Linux display paths:

1. persistent full-screen JPEG upload;
2. native sensor widgets driven by NexLinq-compatible `0x21` telemetry.

## Confirmed working state

Tested on Ubuntu with:

- Device: Phanteks LCD6-HD
- USB VID:PID: `1f3a:6502`
- Firmware: `V1.0.0.10` (`Aug 6 2026` build)
- HID report ID: `0x01`
- HID OUT report: 1024 bytes
- HID IN report: 512 bytes

### Static image path

```text
0x22 verify device
0x2A configure image-background mode
0x28 upload JPEG in acknowledged pages
0x30 apply/commit layout
```

The activation detail that completed the Linux static path was:

```text
Working: 01 30 00 01 00 01 ...
Failed:  01 30 00 01 00 00 ...
```

The applied JPEG survives normal shutdown and complete AC-power removal, so repeated JPEG writes are not appropriate for live telemetry.

### Native live path

Native widgets are physically validated from Linux:

```text
0x30 configure native sensor widget(s)
-> recurring 123-byte 0x21 SetHandshakeData reports
-> 512-byte echo acknowledgements
-> visible graph/value updates
```

The full Linux `0x21` implementation populates source-confirmed CPU/GPU/RAM/NVMe fields from real telemetry. Unsupported CPU/PSU power fields remain zero rather than being fabricated.

The private Linux pipeline now derives the required `0x30` source-specific maximum automatically before starting `native-live`. The validated derivations are:

```text
selectors 7-11 -> 4000 RPM on the validation workstation
selector 28    -> CPU max clock telemetry
selector 31    -> GPU 1 max clock telemetry
selector 32    -> GPU 1 power.max_limit
selector 42    -> vendor packed RAM maximum
```

A continuous selector-32 run was physically validated with startup reporting `source=32, max=390`, 512-byte `0x30` ACK, recurring 512-byte `0x21` ACKs, and visible GPU-power updates varying from roughly 11-17 W.

A frozen native current value is not evidence that host telemetry is still arriving: the LCD retains the last native value after host updates stop. In the selector-32 `native-live` run, the current value remained at the final 12 W after sender stop while the earlier 11 W minimum and 17 W maximum still aged out over approximately one visible graph-history width. Therefore host-update stop freezes the retained current value but does not necessarily freeze rolling-history aging; the firmware mechanism is not claimed.

### Multiple simultaneous native widgets

Multiple native sensor widgets are now physically validated.

Recovered NexLinq code shows that any nonzero layout is serialized as **one `0x30` report per item**, with 50 ms between reports. For each report:

```text
report[3]   = total item count
report[4]   = lcd/item index
report[5]   = layout index
report[6:9] = zero-based item iteration, 24-bit BE
```

The first hardware-tested public path uses stock **layout 10**, which contains three item indices `0`, `1`, and `2`. The validating run configured:

```text
item 0 -> selector 1  CPU temperature
item 1 -> selector 32 GPU power, max 390 W
item 2 -> selector 47 second NVMe temperature field
```

All three configuration packets returned 512-byte acknowledgements. Live telemetry then correlated with the LCD as follows:

```text
CPU 47.75 C       -> LCD 48 C
GPU0 11.86 W      -> LCD 12 W
NVMe1 33.85 C     -> LCD 34 C
```

Fifteen subsequent full `0x21` cycles also returned 512-byte acknowledgements. Three distinct native regions were visible simultaneously.

The `0x30` text1 field is source-confirmed and the public builder now accepts a caller-supplied ASCII label. Compact local labels use `CPU`, `GPU0`, `HD0`, and `HD1`. In the three-panel layout, trailing identifier characters were not separately confirmed as visually legible, so multi-widget/value operation is considered validated while compact-label presentation remains UI work.

## Physically validated native selectors

The public native widget builder is conservatively allowlisted to selectors that were physically exercised from Linux:

| ID | Metric | Validation |
|---:|---|---|
| 1 | CPU temperature | native line graph and live updates |
| 7 | top radiator fan RPM | `0 -> 717 x3`, max 4000 RPM |
| 8 | rear fan RPM | `0 -> 693 x3`, max 4000 RPM |
| 9 | AIO pump RPM | `0 -> 3125 x3`, max 4000 RPM |
| 10 | side fan RPM | `0 -> 539 x3`, max 4000 RPM |
| 11 | bottom fan RPM | `0 -> 498 x3`, max 4000 RPM |
| 27 | CPU utilization | idle rounding and controlled ~25-point load validated |
| 28 | CPU clock | exact same-sample 4373.353 MHz -> 4.37 GHz display |
| 30 | GPU 1 utilization | controlled off-screen GPU load; exact same-sample 71% correlation |
| 31 | GPU 1 clock | 2115 MHz maximum; retained ~1.93 GHz -> fresh 210 MHz transition |
| 32 | GPU 1 power | exact same-sample 9.46 W -> 9 W current display; 390 W maximum |
| 42 | RAM used | retained 3.34 GiB -> fresh ~3.47 GiB transition with vendor RAM max packing |
| 46 | NVMe 0 temperature | first NVMe field physically correlated |
| 47 | NVMe 1 temperature | second NVMe field; live `33 -> 34 C` behavior physically validated |

The generalized builder does **not** expose arbitrary selector ranges.

## `0x30` source-specific maxima

NexLinq's recovered `getMaxValue()` logic confirms that report offsets `17-22` contain three u16 BE source-specific maxima. Relevant mappings include:

```text
fan 7-26 -> configured max RPM
28       -> CPU max clock
29       -> CPU max power
31       -> GPU 1 max clock
32       -> GPU 1 max power
42       -> packed RAM total
43-44    -> 1200 display scale
```

Physically validated examples:

```text
selectors 7-11 fan RPM: 4000 RPM
selector 28 CPU clock: 5756 MHz
selector 31 GPU clock: 2115 MHz
selector 32 GPU power: 390 W
selector 42 RAM used:  0x3c56 on a host with 60.34 GiB OS-visible RAM
```

The private `native-live` path now derives these maxima from the same live telemetry model used to populate `0x21`, and fails clearly if a required clock/power/RAM maximum is unavailable rather than silently sending zero.

### RAM selector 42 packing

The unusual selector-42 maximum is real vendor behavior, not a decompiler artifact.

The installed LCD6-HD, LCD7-HD, and LCD10-HD vendor DLL implementations all construct the RAM-widget maximum as:

```text
(high byte = whole GiB) | (low byte = literal 0x56)
```

On the validation host:

```text
OS-visible RAM total: 60.34 GiB
0x21 RAM-total bytes: 3c 22
0x30 selector-42 max: 3c 56
```

The `0x21` RAM total therefore carries the real hundredths byte (`0x22` = decimal 34), while the `0x30` widget maximum deliberately uses literal `0x56` (decimal 86). The public helper `ram_widget_max_from_total_gib()` reproduces the physically validated vendor rule.

## Line-widget footer/history semantics

The three bottom values in the validated line widget behave as:

```text
left   = minimum of rolling visible history
middle = maximum of rolling visible history
right  = current value
```

Physical testing with GPU clock, CPU clock, RAM used, and GPU power shows that the current value updates first while history-derived min/max values can lag. An old min/max value disappeared only after the graph had advanced across the full visible plotting width, strongly indicating that the footer statistics are tied to the visible rolling history window.

The later continuous selector-32 `native-live` test refined this observation: after the sender stopped at a retained 12 W current value, the earlier 11 W minimum and 17 W maximum still aged out over about one visible graph-history width. This proves only the observed LCD behavior; it does not establish whether firmware advances history by repeating the retained current sample or by another internal mechanism.

Do not overclaim the firmware algorithm: recovered NexLinq JavaScript shows analogous rolling-history min/max/current logic, while physical testing proves only the observed LCD behavior.

One additional UI detail observed with GPU power selector `32`: only the right/current footer value carried the `W` suffix; the left/minimum and middle/maximum values were unitless.

## Recovered source selectors

NexLinq's embedded WebView UI and .NET bridge provide a defensible selector map:

| ID | Metric |
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
| 33-41 | GPU-associated internally, but unassigned/unexposed in the recovered NexLinq UI |
| 42 | RAM used |
| 43 | PSU Power Out |
| 44 | PSU Power In |
| 45 | PSU Efficiency |
| 46-50 | NVMe temperatures |
| 51-55 | SATA temperatures |

IDs `33-41` are deliberately left unresolved rather than guessed.

## Full `0x21` telemetry

The source-confirmed 123-byte payload includes:

- CPU temperature, utilization, current/max clock;
- up to five GPU temperatures;
- 20 fan RPM fields;
- GPU utilization, current/max clock, current/max power, used/total VRAM;
- RAM used/total;
- PSU output/input/efficiency fields;
- NVMe/SATA temperatures.

On the validation workstation, CPU current/max power and PSU fields remain zero because no verified Linux source is available.

For the RTX 3090, NexLinq `PowerMax` maps to NVIDIA `power.max_limit` (390 W on the validation card), not the current software `power.limit` (370 W).

## Public code

`src/phanteks_lcd6.py` contains the validated static-image transport.

`src/phanteks_lcd6_native.py` contains:

- 56-byte and 123-byte `0x21` report builders;
- source-confirmed full-payload encoding;
- echo-ACK validation;
- a strict physically validated `0x30` selector allowlist;
- source-specific maximum-value fields;
- validated RAM selector-42 max packing helper;
- source-confirmed configurable text1 labels;
- physically validated layout-10 three-widget report construction and sending;
- backward-compatible CPU-temperature widget wrappers;
- deliberate zeroing of unsupported CPU/PSU power telemetry.

## Quick start — static JPEG

Use a **1480×720 JPEG**:

```bash
sudo python3 examples/show_jpeg.py /path/to/image.jpg
```

No third-party Python packages are required for the static transport.

## Firmware note

The test unit originally reported `V1.0.0.0` (`Dec 16 2025`). With that firmware, acknowledged image/configuration traffic did not reliably produce the expected visible result, including under official Windows NexLinq during testing.

After the official NexLinq firmware update, the unit reported `V1.0.0.10`. Windows display control began working, packet capture exposed the corrected static `0x30` activation prefix, and Linux static/native control was subsequently validated.

The corrected packet was never tested against the old firmware. Downgrading solely to answer that historical question is not recommended.

## Safety / publication scope

This repository intentionally does not publish:

- Phanteks firmware binaries;
- firmware-update payload captures;
- raw PCAP/PCAPNG captures;
- device serial numbers;
- extracted NexLinq WebView resources;
- decompiled vendor source;
- vendor DLL/EXE files;
- bootloader/reset experiments.

Published code is limited to derived interoperability facts and paths that have been source-confirmed, capture-confirmed, or directly validated on hardware.

## Next work

- additional NVMe/SATA selectors;
- remaining fan selectors only when genuine mapped tachometer RPM sources exist;
- expand beyond the first physically validated three-item layout;
- improve compact-label legibility and placement/sizing/colors/alarm behavior;
- second RTX 3090 behavior after GPU-B is installed;
- service/autostart packaging.

GPU fan percentage from `nvidia-smi` is not physical RPM and is not mapped into native fan selectors.

CPU power selector `29` and PSU selectors `43-45` remain out of live testing until verified local telemetry sources exist.

## Detailed records

- [`PROTOCOL.md`](PROTOCOL.md) — byte-level protocol map
- [`VALIDATION.md`](VALIDATION.md) — physical validation history
- [`STORAGE-MAPPING.md`](STORAGE-MAPPING.md) — NVMe selector/device mapping
- [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md) — methodological acknowledgements

## Project write-up

KLand Studio: https://klandstudio.net/labs/phanteks-lcd6-linux/
