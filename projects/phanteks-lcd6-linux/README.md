# Phanteks LCD6-HD Linux Control

Native Linux control of the **Phanteks LCD6-HD** over USB HID.

This project documents a working Linux path for sending a full-screen JPEG to the LCD6-HD without running Phanteks NexLinq under Windows.

## Confirmed working state

Tested on Ubuntu with:

- Device: Phanteks LCD6-HD
- USB VID:PID: `1f3a:6502`
- Firmware: `V1.0.0.10` (`Aug 6 2026` build)
- HID report ID: `0x01`
- HID OUT report: 1024 bytes
- HID IN report: 512 bytes

The working transaction is:

```text
0x22 verify device
0x2A configure image-background mode
0x28 upload JPEG in acknowledged pages
0x30 activate layout
```

The activation packet was the final breakthrough:

```text
Working: 01 30 00 01 00 01 ...
Failed:  01 30 00 01 00 00 ...
```

Changing that one byte after the firmware update made the uploaded Linux image appear immediately.

## Quick start

Use a **1480×720 JPEG**.

```bash
sudo python3 examples/show_jpeg.py /path/to/image.jpg
```

No third-party Python packages are required.

The example performs all device verification and transport checks before activation. It does **not** flash firmware, enter a bootloader, or send undocumented reset commands.

## Repository layout

```text
projects/phanteks-lcd6-linux/
├── README.md
├── PROTOCOL.md
├── ACKNOWLEDGEMENTS.md
├── SHARE_WITH_NEXTUXLINQ.md
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

- Phanteks firmware binaries
- firmware-update payload captures
- bootloader/reset experiments
- device serial numbers
- raw captures containing unnecessary vendor assets

The current public code is limited to commands observed in the official software and the static-image path we have directly validated.

## Next work

- reproduce the live diagnostics/layout path;
- feed CPU and GPU telemetry from Linux;
- support multi-GPU temperatures;
- add fan/pump data where Linux exposes it;
- turn the transport into a reusable library/daemon.

## Project write-up

KLand Studio: https://klandstudio.net/labs/phanteks-lcd6-linux/

## Acknowledgement

NexTuxLinq by **anoraknophobia** was an important methodological reference for approaching undocumented Phanteks USB devices carefully. See [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md).
