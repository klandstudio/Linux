# Phanteks LCD6-HD Linux Control

Native Linux control of the **Phanteks LCD6-HD** over USB HID.

This project documents a working Linux path for sending a full-screen JPEG to the LCD6-HD without running Phanteks NexLinq under Windows, plus ongoing reverse engineering of the native live-telemetry/widget path.

## Confirmed working state

Tested on Ubuntu with:

- Device: Phanteks LCD6-HD
- USB VID:PID: `1f3a:6502`
- Firmware: `V1.0.0.10` (`Aug 6 2026` build)
- HID report ID: `0x01`
- HID OUT report: 1024 bytes
- HID IN report: 512 bytes

The hardware-validated static transaction is:

```text
0x22 verify device
0x2A configure image-background mode
0x28 upload JPEG in acknowledged pages
0x30 apply/commit layout
```

The activation packet was the original breakthrough:

```text
Working: 01 30 00 01 00 01 ...
Failed:  01 30 00 01 00 00 ...
```

The current Linux implementation also waits for the observed successful `0x30` acknowledgement instead of treating activation as fire-and-forget.

The exact validation history is preserved in [`VALIDATION.md`](VALIDATION.md).

## Static image persistence

The applied static JPEG survives a normal shutdown and complete AC power removal. On the next cold boot the LCD restores the previously uploaded Panda dashboard without another Linux image transfer.

That means repeated JPEG uploads are **not** the right mechanism for live telemetry. The static JPEG is best treated as a persistent background/fallback.

## Native telemetry status

The native telemetry path is now physically validated from Linux:

```text
0x30 configure native sensor widget
-> recurring 123-byte 0x21 SetHandshakeData reports
-> acknowledged on-device graph updates
```

A capture-derived line-graph configuration produced a 512-byte acknowledgement and displayed a native CPU-temperature graph. A Linux live loop then sent one full `0x21` report per second. Every observed report received a 512-byte echo acknowledgement, and the graph visibly advanced several times as new values arrived.

Stopping the Linux sender with Ctrl+C stops fresh telemetry but does not clear the LCD. The device retains the last native layout/value, matching the behavior previously observed when Windows NexLinq stopped. A still-visible graph is therefore not evidence that fresh values are arriving.

Offline inspection of NexLinq's installed .NET assembly subsequently confirmed the full 123-byte telemetry schema, including CPU utilization/clock/power, up to five GPUs, twenty fans, RAM, PSU values, and disk temperatures. The current private Linux pipeline still populates only the already-tested temperature and fan portion; implementation and hardware validation of the additional decoded fields remain pending.

See [`PROTOCOL.md`](PROTOCOL.md) for byte-level details and [`VALIDATION.md`](VALIDATION.md) for the physical test record.

## Quick start — static JPEG

Use a **1480×720 JPEG**.

```bash
sudo python3 examples/show_jpeg.py /path/to/image.jpg
```

No third-party Python packages are required.

The public `src/` code is a cleaned refactor of the hardware-validated static sequence. The raw sequence and activation bytes are confirmed on the test unit; this remains an early implementation and should still be treated cautiously on other devices/firmware versions.

The example performs device verification and transport checks before activation. It does **not** flash firmware, enter a bootloader, or send undocumented reset commands.

## Repository layout

```text
projects/phanteks-lcd6-linux/
├── README.md
├── PROTOCOL.md
├── VALIDATION.md
├── ACKNOWLEDGEMENTS.md
├── src/
│   └── phanteks_lcd6.py
└── examples/
    ├── probe.py
    └── show_jpeg.py
```

## Firmware note

The test unit originally reported `V1.0.0.0` (`Dec 16 2025`). With that firmware, both reconstructed Linux image transactions and official Windows NexLinq screen changes could complete over USB without producing the expected visible result.

After the official NexLinq firmware update, the unit reported `V1.0.0.10`. Windows display control began working, and packet capture of a successful Windows transaction exposed the corrected `0x30` activation prefix above.

We have **not** tested the corrected `0x30` packet on the old firmware and do not recommend downgrading to find out.

## Safety / scope

This repository intentionally does not contain:

- Phanteks firmware binaries;
- firmware-update payload captures;
- bootloader/reset experiments;
- device serial numbers;
- large raw packet captures containing unnecessary vendor assets.

The current public code is limited to commands observed in the official software and directly validated during this work.

## Next work

- map every native widget source-selector ID to its human-readable sensor;
- populate and validate the newly decoded `0x21` CPU/GPU/RAM fields from Linux;
- support multiple native widgets and both RTX 3090s after the second GPU is installed;
- recover placement, sizing, and color behavior without guessing undocumented values;
- determine whether native fault/warning status can support color/visibility/blinking safely;
- turn the transport into a reusable library/daemon after the widget path is proven.

## Project write-up

KLand Studio: https://klandstudio.net/labs/phanteks-lcd6-linux/

## Acknowledgement

NexTuxLinq by **anoraknophobia** was an important methodological reference for approaching undocumented Phanteks USB devices carefully. See [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md).
