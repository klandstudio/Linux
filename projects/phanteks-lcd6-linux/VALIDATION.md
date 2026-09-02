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

This validates the static JPEG path on the tested firmware. It does not yet validate live diagnostics, all orientations/layouts, other firmware versions, or every field in the larger NexLinq telemetry packet.
