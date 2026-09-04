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
0x30 configure native sensor widget
-> recurring 123-byte 0x21 SetHandshakeData reports
-> 512-byte echo acknowledgements
-> visible graph/value updates
```

The full Linux `0x21` implementation populates source-confirmed CPU/GPU/RAM/NVMe fields from real telemetry. Unsupported CPU/PSU power fields remain zero rather than being fabricated.

A frozen native widget is not evidence that host telemetry is still arriving: the LCD retains the last native layout/value after host updates stop.

## Physically validated native selectors

The public native widget builder is conservatively allowlisted to selectors that were physically exercised from Linux:

| ID | Metric | Validation |
|---:|---|---|
| 1 | CPU temperature | native line graph and live updates |
| 27 | CPU utilization | idle rounding and controlled ~25-point load validated |
| 28 | CPU clock | exact same-sample 4373.353 MHz -> 4.37 GHz display |
| 30 | GPU 1 utilization | controlled off-screen GPU load; exact same-sample 71% correlation |
| 31 | GPU 1 clock | 2115 MHz maximum; retained ~1.93 GHz -> fresh 210 MHz transition |
| 32 | GPU 1 power | exact same-sample 9.46 W -> 9 W current display; 390 W maximum |
| 42 | RAM used | retained 3.34 GiB -> fresh ~3.47 GiB transition with vendor RAM max packing |
| 46 | NVMe 1 temperature | 45.85 °C source -> 46 °C display |

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
selector 28 CPU clock: 5756 MHz
selector 31 GPU clock: 2115 MHz
selector 32 GPU power: 390 W
selector 42 RAM used:  0x3c56 on a host with 60.34 GiB OS-visible RAM
```

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

- physically validate the first five mapped fan selectors `7-11` using vendor-valid configured max RPM values;
- automatic selector-to-max derivation in the private Linux pipeline;
- fix/extend `native-live` for max-dependent selectors;
- additional NVMe/SATA selectors;
- device-name / label generalization;
- multiple simultaneous native widgets;
- placement, sizing, colors, and alarm behavior;
- second RTX 3090 behavior after GPU-B is installed;
- service/autostart packaging.

CPU power selector `29` and PSU selectors `43-45` remain out of live testing until verified local telemetry sources exist.

## Detailed records

- [`PROTOCOL.md`](PROTOCOL.md) — byte-level protocol map
- [`VALIDATION.md`](VALIDATION.md) — physical validation history
- [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md) — methodological acknowledgements

## Project write-up

KLand Studio: https://klandstudio.net/labs/phanteks-lcd6-linux/
