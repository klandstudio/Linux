# Validation record

## Static-image control — confirmed

Date: 2026-09-01

Device firmware reported immediately before the test:

```text
W2,1A18C,AIO,FDT,LCD6-HD,V1.0.0.10,Aug  6 2026,13:53:58
```

The Linux test used the established `0x2A -> 0x28 -> 0x30` sequence with one change from the previous failed implementation:

```text
old activation prefix: 01 30 00 01 00 00
new activation prefix: 01 30 00 01 00 01
```

The run completed as follows:

```text
Using /dev/hidraw4
Verified: W2,1A18C,AIO,FDT,LCD6-HD,V1.0.0.10,Aug  6 2026,13:53:58
1/3 Configuring background-only landscape mode...
Exact configuration echo received; report accepted.
2/3 Uploading the test-card JPEG...
Uploading 173,096 bytes in 172 acknowledged packets...
First image packet received a matching page acknowledgement.
   10% (18/172)
   20% (35/172)
   30% (52/172)
   40% (69/172)
   50% (86/172)
   60% (104/172)
   70% (121/172)
   80% (138/172)
   90% (155/172)
  100% (172/172)
3/3 Sending background-only layout commit (0x30)...
Complete sequence sent in one uninterrupted HID session.
```

Physical result: the LCD immediately switched to the uploaded 1480×720 test image.

A later capture of a successful static-image transaction established the more precise sequencing now used in the public implementation:

- about 117 ms between the `0x2A` acknowledgement and first `0x28` JPEG packet;
- about 105 ms between the final `0x28` acknowledgement and `0x30` apply;
- `0x30` apply response at report offset 11 = `0x01`.

The Linux static sender was updated to use a 120 ms pre-upload delay, a 100 ms pre-apply delay, and to require the observed `0x30` success response.

## Static-image persistence — confirmed

Date: 2026-09-03

After a successful Linux dashboard upload, no `panda_lcd` sender process, user service, system service, or autostart entry was running.

The host was then shut down normally, PSU power was removed, and the system remained without AC power for roughly 30 seconds.

On cold power-up the LCD showed the previously uploaded Panda dashboard again without a new Linux image transfer.

Observed startup sequence:

```text
Panda dashboard -> brief Phanteks screen -> Panda dashboard
```

This confirms that the applied static image/configuration is retained by the LCD/controller across complete power loss. Routine live telemetry therefore should not be implemented by repeatedly writing JPEGs with `0x28`.

## Native `0x21` telemetry transport — confirmed

Date: 2026-09-03

### 56-byte form

Linux sent one short `0x21` SetHandshakeData packet containing live CPU/GPU/fan values.

Representative values:

```text
CPU: 36.25 C
GPU temps: [33.0]
Fan RPMs [top,rear,pump,side,bottom]: [704, 665, 3116, 552, 492]
```

The device returned a 512-byte acknowledgement whose payload matched the transmitted 56-byte payload.

Wireshark captured the expected HID OUT/IN transaction pair.

No reliable visual observation was recorded for the first short-form test because the LCD was not being watched at the moment of transmission.

### 123-byte form

Linux was then extended to reproduce NexLinq's normal 123-byte (`0x007b`) telemetry packet shape while deliberately leaving currently-undecoded bytes 56-122 as zero.

The LCD was watched continuously during this test.

Representative values:

```text
CPU: 35.75 C
GPU temps: [33.0]
Fan RPMs [top,rear,pump,side,bottom]: [677, 698, 3116, 554, 497]
```

Result:

```text
Sent one 0x21 packet (123-byte full) to /dev/hidraw4; ACK length=512
```

The acknowledgement payload matched the transmitted 123-byte payload.

Physical result: **no visible change**.

The LCD continued showing the static Panda dashboard, including the old baked-in clock value `20:37:06`. This confirms that the visible clock was still part of the persistent JPEG and that accepted `0x21` telemetry does not by itself create or enable a native widget in the background-only layout.

Private reference captures retained outside this public repository:

```text
linux_0x21_single_known_good.pcapng
linux_0x21_full_123_no_visual.pcapng
```

They are intentionally not committed because the public repository does not need large raw captures to document the validated behavior.

## Current boundary

Validated now:

- static JPEG upload and activation from Linux;
- static image retention across full power loss;
- `0x21` 56-byte telemetry transport and echo acknowledgement;
- `0x21` 123-byte telemetry transport and echo acknowledgement;
- Linux fan ordering correlation for top/rear/pump/side/bottom.

Not yet validated:

- native widget/layout configuration sufficient to render Linux `0x21` values;
- arbitrary native text, color, visibility, or blinking;
- all fields in the 123-byte NexLinq telemetry payload;
- all orientations/layouts or other firmware versions.

The next protocol target is the exact Windows `0x30` widget/configuration transaction that binds native widgets to the live `0x21` data stream.
