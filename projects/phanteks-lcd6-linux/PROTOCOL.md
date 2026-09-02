# Phanteks LCD6-HD protocol notes

These notes describe behavior observed from Phanteks NexLinq traffic and validated against a real LCD6-HD. They are not an official Phanteks specification.

## USB identity

- VID:PID: `1f3a:6502`
- USB 2.0 High Speed composite device
- HID usage page observed: `0xff1b`
- HID usage observed: `0x91`
- HID report ID: `0x01`
- HID OUT report size: 1024 bytes
- HID IN report size: 512 bytes

The device also exposes a vendor-specific bulk interface. The confirmed static-image path described here uses the HID interface.

## Confirmed commands

### `0x22` — device information

A 1024-byte OUT report with:

```text
offset 0: 01
offset 1: 22
remaining bytes: 00
```

returns a 512-byte IN report. The payload starts at offset 11 and contains comma-separated device metadata, including product and firmware version.

Observed firmware strings on the test unit:

```text
W2,1A18C,AIO,FDT,LCD6-HD,V1.0.0.0,Dec 16 2025,14:57:39
W2,1A18C,AIO,FDT,LCD6-HD,V1.0.0.10,Aug  6 2026,13:53:58
```

### `0x2A` — LCD configuration

The validated Linux background-image configuration uses a 1024-byte OUT report:

| Offset | Meaning | Validated value |
| --- | --- | --- |
| 0 | report ID | `0x01` |
| 1 | command | `0x2A` |
| 9-10 | payload length, big-endian | `0x0009` |
| 11 | layout/mode | `0x00` background-only |
| 12 | brightness | `70` in Linux validation |
| 13 | orientation | `0x00` landscape |
| 14 | background mode | `0x00` image |
| 15 | flags | `0x00` |
| 16-19 | ARGB fallback | `ff 00 00 00` |

The test unit returned an exact 512-byte prefix echo for this report after the firmware update.

The working client waits about 50 ms before starting image transfer.

### `0x28` — JPEG transfer

The JPEG is split across acknowledged 1024-byte OUT reports.

| Offset | Meaning |
| --- | --- |
| 0 | report ID `0x01` |
| 1 | command `0x28` |
| 2-5 | total JPEG byte length, big-endian |
| 6-8 | zero-based page number, 24-bit big-endian |
| 9-10 | current JPEG chunk length + 1, big-endian |
| 11 | media slot; `0xFF` = background |
| 12+ | up to 1012 JPEG bytes |

The device acknowledges each page with an IN report whose page number at offsets 6-8 matches the transmitted page. Do not advance to the next page until the expected acknowledgement is received.

A validated Linux test transferred a 173,096-byte JPEG in 172 acknowledged packets.

### `0x30` — layout activation

This was the final missing piece for visible Linux control.

The successful Windows static-image capture contained a host-to-device HID payload beginning:

```text
01 30 00 01 00 01 ...
```

The earlier Linux reconstruction sent:

```text
01 30 00 01 00 00 ...
```

After changing only the sixth byte from `00` to `01`, the same Linux `0x2A -> 0x28 -> 0x30` sequence immediately displayed the uploaded test image on firmware `V1.0.0.10`.

The working public implementation therefore emits:

```text
01 30 00 01 00 01 00 00 00 ...
```

for the 1024-byte activation report.

The official library does not wait for a `0x30` response.

### `0x21` — telemetry / handshake data

A short 56-byte payload form was recovered and accepted during Linux testing. Its payload is copied starting at report offset 11.

| Payload offset | Meaning |
| --- | --- |
| 0-3 | Unix timestamp, big-endian |
| 4 | UTC-state byte |
| 10 | CPU temperature |
| 11-15 | up to five GPU temperatures |
| 16-55 | up to twenty fan RPM values, 2 bytes each, big-endian |

The real NexLinq application also sends a larger 123-byte telemetry form. Live diagnostics are not yet considered fully reproduced, so `0x21` is documented but intentionally not exposed as a stable public API in the first code drop.

## Confirmed static-image sequence

```text
open one HID session
  -> 0x22 verify
  -> 0x2A configure
  -> wait ~50 ms
  -> 0x28 page 0 / wait for ACK
  -> 0x28 page 1 / wait for ACK
  -> ...
  -> 0x28 final page / wait for ACK
  -> wait ~100 ms
  -> 0x30 activate using 01 30 00 01 00 01 ...
  -> no 0x30 response required
close HID session
```

## Firmware finding

On firmware `V1.0.0.0`, image transfers could be acknowledged without the expected visible display change, including under the official Windows application during testing.

After the official NexLinq firmware update to `V1.0.0.10`, Windows display control worked. The successful capture from that state then exposed the corrected `0x30` activation byte, and Linux static-image control was confirmed.

This does **not** prove which failure belonged to firmware versus the earlier Linux activation packet. The corrected packet was never tested against the old firmware, and there is no reason to downgrade solely to answer that historical question.

## Not published here

The project does not redistribute vendor firmware, firmware-update payloads, or unnecessary raw captures. Firmware-update traffic was useful for understanding device behavior, but it is outside the scope of the public control implementation.
