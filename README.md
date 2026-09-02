# Linux

Practical Linux hardware projects, reverse engineering, and tooling from KLand Studio.

## Projects

### Phanteks LCD6-HD Linux Control

Native Linux control of the Phanteks LCD6-HD over USB HID.

**Status:** static JPEG display control is confirmed working on Ubuntu with LCD firmware `V1.0.0.10`.

The first proven display path is:

```text
0x2A configure -> acknowledged 0x28 JPEG pages -> 0x30 activate
```

The activation detail that completed the Linux implementation was:

```text
Working: 01 30 00 01 00 01 ...
Failed:  01 30 00 01 00 00 ...
```

See [`projects/phanteks-lcd6-linux/`](projects/phanteks-lcd6-linux/) for the code, protocol notes, and reproducible example.

Project write-up: https://klandstudio.net/labs/phanteks-lcd6-linux/

## Scope

This repository is intended to hold Linux-focused projects that are useful beyond one machine. Experimental captures, vendor firmware payloads, private hardware identifiers, and unrelated workstation notes are kept out of the public repository.
