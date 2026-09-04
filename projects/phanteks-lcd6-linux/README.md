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

Native widgets are now physically validated from Linux:

```text
0x30 configure native CPU sensor widget
-> recurring 123-byte 0x21 SetHandshakeData reports
-> 512-byte echo acknowledgements
-> visible graph updates
```

A thirty-cycle `native-live` run visibly advanced the CPU-temperature graph several times. Stopping the sender leaves the last native layout/value visible; a frozen graph is therefore not evidence that telemetry is still arriving.

On September 4, 2026 the Linux implementation was extended from a 123-byte packet with zero-filled trailing fields to a **source-confirmed, populated full telemetry packet**. The LCD accepted the expanded report and the native CPU graph advanced by one sample during the validation send.

The currently populated Linux fields include:

- CPU temperature, utilization, current clock, maximum clock;
- up to five GPU temperatures;
- fan RPM values;
- GPU utilization, current/max clock, current power, used/total VRAM, maximum power;
- RAM used/total;
- NVMe temperature.

CPU power, CPU maximum power, and PSU telemetry remain zero on the validation workstation because no verified Linux source was available. Missing telemetry is intentionally left zero rather than fabricated.

## Recovered source selectors

NexLinq's embedded WebView UI and .NET bridge now provide a defensible selector map:

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

The recovered LCD6-HD menu currently creates GPU entries for source `2`, `30`, `31`, and `32` using the first GPU. IDs `33-41` are deliberately left unresolved rather than guessed.

## Public code

`src/phanteks_lcd6.py` contains the validated static-image transport.

`src/phanteks_lcd6_native.py` contains the cleaned native-widget / telemetry implementation from the current milestone:

- 56-byte and 123-byte `0x21` report builders;
- source-confirmed full-payload encoding;
- echo-ACK validation;
- the physically validated CPU-temperature native widget `0x30` builder;
- explicit zeroing of unsupported CPU/PSU power telemetry.

The public native widget builder intentionally remains CPU-temperature-only. Generalizing selectors is the next milestone; arbitrary selector probing is not exposed.

## Quick start — static JPEG

Use a **1480×720 JPEG**:

```bash
sudo python3 examples/show_jpeg.py /path/to/image.jpg
```

No third-party Python packages are required for the static transport.

## Repository layout

```text
projects/phanteks-lcd6-linux/
├── README.md
├── PROTOCOL.md
├── VALIDATION.md
├── ACKNOWLEDGEMENTS.md
├── src/
│   ├── phanteks_lcd6.py
│   └── phanteks_lcd6_native.py
└── examples/
    ├── probe.py
    └── show_jpeg.py
```

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
- bootloader/reset experiments.

Published code is limited to derived interoperability facts and paths that have been source-confirmed, capture-confirmed, or directly validated on hardware.

## Next work

- generalize the `0x30` native widget builder to known selector IDs without arbitrary probing;
- validate CPU load, GPU load/power/clock, RAM, and NVMe native widgets one at a time;
- support multiple simultaneous native widgets and both RTX 3090s after the second GPU is installed;
- recover placement, sizing, color, and alarm behavior without guessing undocumented fields;
- add CPU/PSU power only if a real Linux telemetry source is found;
- turn the validated transport into a reusable service after the widget path is generalized.

## Detailed records

- [`PROTOCOL.md`](PROTOCOL.md) — byte-level protocol map
- [`VALIDATION.md`](VALIDATION.md) — physical validation history
- [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md) — methodological acknowledgements

## Project write-up

KLand Studio: https://klandstudio.net/labs/phanteks-lcd6-linux/
