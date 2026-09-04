# Storage / NVMe mapping

This file records the validation workstation's stable UI naming for NVMe temperature selectors separately from motherboard slot numbering.

## UI naming convention

The LCD/project uses zero-based generic names, matching the existing GPU convention:

```text
NVMe 0 -> selector 46 -> Linux nvme0
NVMe 1 -> selector 47 -> Linux nvme1
```

The on-screen names should remain `NVMe 0` and `NVMe 1`. They should not be renamed to motherboard M.2 slot numbers such as `NVMe 3`.

## Current hardware identity

### NVMe 0

```text
selector: 46
Linux device: nvme0
model: Samsung SSD 990 PRO 2TB
physical motherboard slot: M2_1 (user-confirmed installation)
```

### NVMe 1

```text
selector: 47
Linux device: nvme1
model: UMIS RPJTJ128MKP1MDY
capacity: 128 GB nominal / ~119.2 GiB block-device size
physical motherboard slot: M2_3 or M2_4; exact slot not re-verified
```

Do not infer the UMIS physical M.2 slot solely from Linux PCI enumeration or negotiated PCIe width. Update this file if the chassis is opened and the slot is physically confirmed.

## Selector 47 physical validation

Date: 2026-09-04

Linux hwmon mapping was verified directly:

```text
hwmon1 -> nvme0 -> Samsung SSD 990 PRO 2TB
hwmon2 -> nvme1 -> UMIS RPJTJ128MKP1MDY
```

The private collector was extended to preserve one composite temperature per NVMe device in Linux enumeration order. During offline packet construction:

```text
NVMe temperatures: [37.85, 32.85]
0x21 NVMe bytes:    [38, 33, 0, 0, 0]
0x30 selector:      [47, 47, 47]
0x30 max bytes:     00 00 00 00 00 00
```

A live native-widget run using selector 47 produced:

```text
0 -> 33 °C
later -> 34 °C
```

The process continuously received 512-byte `0x21` acknowledgements and stopped cleanly. A post-run source check still showed the second NVMe composite source at 32.85 °C, consistent with normal whole-degree rounding and the observed temperature increase during the run.

Conclusion: selector 47 is physically validated as the second NVMe temperature field, exposed in this project as `NVMe 1`.
