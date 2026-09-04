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

The device also exposes a vendor-specific bulk interface. The confirmed static-image and telemetry paths described here use the HID interface.

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

### `0x2A` — LCD configuration / prepare

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

The successful static-image capture used the following pre-upload form:

```text
01 2a 00 00 00 00 00 00 00 00 09 00 64 00 00 00 ff ...
```

This is distinct from the diagnostic/delete form seen in NexLinq traffic, which contains `...64 ff 00 ff...` in the corresponding payload area.

The device returned an exact 512-byte prefix echo for the static pre-upload report on firmware `V1.0.0.10`.

A successful Windows static-image capture began JPEG transfer about 117 ms after the `0x2A` acknowledgement. The current Linux implementation waits 120 ms.

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

In the successful Windows static sequence, the first `0x28` response carried a status-like value `0x01` and the final page response carried `0x02`. The Linux implementation currently validates page numbering; the exact semantics of those status values remain intentionally undocumented.

### `0x30` — apply / commit / widget configuration

`0x30` is broader than a simple background selector. It appears in static-image activation, diagnostic configuration, delete/reset completion, and video application.

For the static-image path, the successful Windows request begins:

```text
01 30 00 01 00 01 ...
```

The earlier failed Linux reconstruction sent:

```text
01 30 00 01 00 00 ...
```

The corrected Linux request is therefore:

```text
01 30 00 01 00 01 00 00 00 ...
```

The successful Windows static request received a `0x30` response whose payload byte at report offset 11 was `0x01`. The current Linux implementation now waits for this response and requires that success value.

Successful Windows sequencing sent the static `0x30` roughly 105 ms after the final `0x28` response; the Linux implementation waits 100 ms.

Other captured `0x30` observations:

- diagnostic/widget configuration uses request state byte `0x02` at report offset 11;
- graph style byte at offset 12: `0x03 = line`, `0x02 = bar`;
- widget frequency byte at offset 26: `0x01 = 1 sec`, `0x0A = 10 sec`, `0x3C = 60 sec`;
- successful video application used request state byte `0x03` and received response status `0x01`.

These observations are useful for reconstructing the native widget path, but the full widget layout structure is not yet considered decoded.

### `0x21` — telemetry / SetHandshakeData

Two HID telemetry forms have now been sent successfully from Linux and acknowledged by the LCD.

A 56-byte payload form is understood well enough to populate basic sensors. The payload is copied starting at report offset 11, and report offsets 9-10 contain the big-endian payload length.

| Payload offset | Meaning |
| --- | --- |
| 0-3 | Unix timestamp, big-endian |
| 4 | UTC-state byte |
| 10 | CPU temperature |
| 11-15 | up to five GPU temperatures |
| 16-55 | up to twenty fan RPM values, 2 bytes each, big-endian |

The real NexLinq application normally sends a larger 123-byte (`0x007b`) payload. Linux now reproduces that packet shape as well. Bytes 56-122 are not yet decoded and were deliberately zero-filled during the first Linux test.

Validated Linux behavior on 2026-09-03:

```text
56-byte 0x21  -> accepted, 512-byte echo ACK
123-byte 0x21 -> accepted, 512-byte echo ACK
```

Known fan order from Windows captures and Linux correlation:

```text
top, rear, pump, side, bottom
```

A one-shot 123-byte Linux test sent approximately:

```text
CPU 35.75 C
GPU0 33 C
fans 677, 698, 3116, 554, 497 RPM
```

and received a valid echo acknowledgement.

Neither the 56-byte nor 123-byte one-shot packet produced a visible change while the LCD was showing a background-only static layout. The on-screen clock remained the timestamp baked into the JPEG. This is strong evidence that `0x21` is the live data transport, while a separate native widget/layout configuration is required to render those values.

Do not infer that arbitrary text, color, visibility, or blinking can be controlled through `0x21` alone. That remains unproven.

## Confirmed static-image sequence

```text
open one HID session
  -> 0x22 verify
  -> 0x2A configure
  -> wait ~120 ms
  -> 0x28 page 0 / wait for ACK
  -> 0x28 page 1 / wait for ACK
  -> ...
  -> 0x28 final page / wait for ACK
  -> wait ~100 ms
  -> 0x30 apply using 01 30 00 01 00 01 ...
  -> wait for 0x30 response status 0x01
close HID session
```

## Persistence finding

The successfully applied static JPEG survives a complete host shutdown and removal of AC power from the system. On the next cold power-up the previously uploaded Panda dashboard returned without any Linux sender or boot-time service running.

This means repeated `0x28` uploads are not appropriate for routine live telemetry. The persistent JPEG should be treated as a fallback/background asset, while live sensor values should use the native telemetry/widget mechanism once that layout path is fully decoded.

## Firmware finding

On firmware `V1.0.0.0`, image transfers could be acknowledged without the expected visible display change, including under the official Windows application during testing.

After the official NexLinq firmware update to `V1.0.0.10`, Windows display control worked. The successful capture from that state then exposed the corrected `0x30` activation byte, and Linux static-image control was confirmed.

This does **not** prove which failure belonged to firmware versus the earlier Linux activation packet. The corrected packet was never tested against the old firmware, and there is no reason to downgrade solely to answer that historical question.

## Video note

Successful Windows video playback uses the vendor-specific bulk path rather than the HID JPEG path. Captured transfer command `0x51` sends large chunks and is followed by a `0x30` application request using state byte `0x03`. This path is documented only as a protocol observation and is not currently exposed by the Linux implementation.

## Not published here

The project does not redistribute vendor firmware, firmware-update payloads, or unnecessary raw captures. Raw Linux/Windows captures are retained privately for validation but are intentionally not committed to this public repository.
