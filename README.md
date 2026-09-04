# Linux

Practical Linux hardware projects, reverse engineering, and tooling from KLand Studio.

## Projects

### Phanteks LCD6-HD Linux Control

Native Linux control of the Phanteks LCD6-HD over USB HID.

**Status:** static JPEG control, native CPU-temperature graph updates, and a populated source-confirmed 123-byte live telemetry payload are physically validated on Ubuntu with LCD firmware `V1.0.0.10`.

The static display path is:

```text
0x2A configure -> acknowledged 0x28 JPEG pages -> 0x30 activate
```

The activation detail that completed the Linux implementation was:

```text
Working: 01 30 00 01 00 01 ...
Failed:  01 30 00 01 00 00 ...
```

The native live path is:

```text
0x30 configure native sensor widget
-> recurring 123-byte 0x21 telemetry reports
-> 512-byte echo acknowledgements
-> on-device graph updates
```

The full telemetry implementation now carries real Linux CPU utilization/clock data, GPU utilization/clock/power/VRAM data, RAM values, fans, and NVMe temperature. CPU/PSU power fields remain zero where the host exposes no verified source.

NexLinq's embedded UI was also recovered far enough to map the documented source-selector IDs for CPU, GPU, fans, RAM, PSU, NVMe, and SATA without arbitrary HID probing.

See [`projects/phanteks-lcd6-linux/`](projects/phanteks-lcd6-linux/) for code, protocol notes, and the physical validation record.

Project write-up: https://klandstudio.net/labs/phanteks-lcd6-linux/

### ENE DRAM Persistent RGB Save

Persistent cold-boot static RGB for ENE/Aura-compatible memory.

**Status:** confirmed across full power loss on a Silicon Power XPOWER Zenith RGB DDR5 kit. The project documents OpenRGB's hidden ENE save gate and a conservative SignalRGB `ENE_RAM.js` patch that adds a one-shot nonvolatile static-color save.

The ENE save sequence centers on:

```text
0x8021 <- 0x01   # Static mode
0x8020 <- 0x00   # Internal/effect mode
0x80A0 <- 0xAA   # Save persistent state
```

See [`projects/ene-dram-persistent-rgb/`](projects/ene-dram-persistent-rgb/) for the tested procedure, safety notes, OpenRGB configuration, SignalRGB patch, rollback steps, and register references.

## Scope

This repository is intended to hold Linux-focused hardware projects, reverse engineering, and reusable tooling. Cross-platform companion tools are included when they are part of a Linux-originated hardware investigation. Experimental captures, vendor firmware payloads, private hardware identifiers, extracted vendor assets, and unrelated workstation notes are kept out of the public repository.
