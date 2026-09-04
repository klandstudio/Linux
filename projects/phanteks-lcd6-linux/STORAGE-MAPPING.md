# Storage / NVMe mapping

This file records the validation workstation's stable selector/device naming separately from motherboard slot numbering.

## UI naming convention

The project keeps zero-based storage identity, matching Linux enumeration and the existing GPU convention:

```text
NVMe 0 -> selector 46 -> Linux nvme0
NVMe 1 -> selector 47 -> Linux nvme1
```

For documentation and device identity, use `NVMe 0` and `NVMe 1`; do not rename a device to a motherboard slot number such as `NVMe 3`.

For **compact native LCD panels**, the selected short labels are:

```text
HD0 -> NVMe 0 -> selector 46
HD1 -> NVMe 1 -> selector 47
```

The `HD0` / `HD1` strings are display aliases only. They do not change Linux device enumeration or the selector mapping.

## Current hardware identity

### NVMe 0 / HD0

```text
selector: 46
Linux device: nvme0
model: Samsung SSD 990 PRO 2TB
physical motherboard slot: M2_1 (user-confirmed installation)
```

### NVMe 1 / HD1

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

Conclusion: selector 47 is physically validated as the second NVMe temperature field, exposed in project documentation as `NVMe 1` and in compact native-panel UI as `HD1`.

## Compact-label validation boundary

The source-confirmed `0x30` text1 field accepts the new short labels, but the first three-panel physical test did **not** separately prove that trailing numeric suffixes are visually legible at that panel size. An apparent `1` in the earlier `NVMe 1` label was actually a vertical divider.

Therefore `HD0` / `HD1` are the chosen compact naming convention, while exact rendered suffix legibility remains a presentation/layout task rather than a completed protocol validation.
