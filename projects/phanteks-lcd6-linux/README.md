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

Linux now successfully sends and receives acknowledgements for both known `0x21` SetHandshakeData forms:

```text
56-byte payload  -> accepted, echo ACK
123-byte payload -> accepted, echo ACK
```

The decoded portion currently includes:

- Unix timestamp;
- CPU temperature;
- up to five GPU temperatures;
- fan RPM values.

The 123-byte form matches NexLinq's normal packet length. Bytes 56-122 remain intentionally undecoded.

A watched one-shot 123-byte Linux test produced **no visible change** while the display was in background-only mode. The LCD continued showing the old clock value baked into the JPEG. This establishes an important boundary: `0x21` is a working live-data transport, but it does not itself create or enable the widgets that render those values.

The next protocol target is the exact Windows `0x30` widget/configuration transaction that binds native widgets to the `0x21` data stream.

See [`PROTOCOL.md`](PROTOCOL.md) for byte-level details.

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

- decode and reproduce the native widget/layout `0x30` configuration;
- make Linux `0x21` telemetry values visibly render without repeated JPEG uploads;
- decode the remaining 123-byte telemetry fields;
- support multi-GPU temperatures and fan/pump telemetry in the live path;
- determine whether native fault/warning status can support color/visibility/blinking safely;
- turn the transport into a reusable library/daemon after the widget path is proven.

## Project write-up

KLand Studio: https://klandstudio.net/labs/phanteks-lcd6-linux/

## Acknowledgement

NexTuxLinq by **anoraknophobia** was an important methodological reference for approaching undocumented Phanteks USB devices carefully. See [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md).
