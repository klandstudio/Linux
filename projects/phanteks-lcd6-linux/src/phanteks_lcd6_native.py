#!/usr/bin/env python3
"""Native sensor-widget and 0x21 telemetry helpers for Phanteks LCD6-HD.

Derived from traffic produced by the official NexLinq application and validated
against a real LCD6-HD on firmware V1.0.0.10. This module intentionally keeps
unknown/unavailable telemetry fields zero rather than inventing values.

The existing sibling module ``phanteks_lcd6.py`` provides HID discovery,
open/write/read helpers, and the validated static-JPEG transport.
"""

from __future__ import annotations

import time

from phanteks_lcd6 import (
    ACTIVATE_LAYOUT,
    REPORT_ID,
    REPORT_IN,
    REPORT_OUT,
    wait_for_report,
    write_report,
)

SET_HANDSHAKE_DATA = 0x21
TELEMETRY_SHORT_PAYLOAD_SIZE = 56
TELEMETRY_FULL_PAYLOAD_SIZE = 123


def _u8(value) -> int:
    if value is None:
        return 0
    return max(0, min(255, int(round(value))))


def _u16(value) -> bytes:
    if value is None:
        value = 0
    value = max(0, min(65535, int(round(value))))
    return value.to_bytes(2, "big")


def _ram_gib(value) -> bytes:
    """Encode NexLinq's [whole GiB, hundredths] representation."""
    if value is None:
        return b"\x00\x00"
    rounded = round(float(value) + 1e-9, 2)
    whole = int(rounded)
    hundredths = int(round((rounded - whole) * 100))
    if hundredths >= 100:
        whole += 1
        hundredths = 0
    return bytes((max(0, min(255, whole)), max(0, min(99, hundredths))))


def _field(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def build_telemetry_report(
    cpu_temp_c,
    gpu_temps_c=(),
    fan_rpms=(),
    *,
    full=False,
    cpu_util_pct=None,
    cpu_clock_mhz=None,
    cpu_clock_max_mhz=None,
    ram_used_gib=None,
    ram_total_gib=None,
    gpu_stats=(),
    nvme_temps_c=(),
    sata_temps_c=(),
):
    """Build source-confirmed 0x21 SetHandshakeData report.

    ``gpu_stats`` items may be objects or dictionaries with these fields:
    util_pct, clock_mhz, power_w, mem_used_mib, clock_max_mhz, power_max_w,
    and mem_total_mib.

    CPU power, CPU max power, and PSU fields are deliberately left zero by
    this cleaned public implementation because the validation workstation did
    not expose a verified Linux telemetry source for them.
    """
    payload_size = (
        TELEMETRY_FULL_PAYLOAD_SIZE if full else TELEMETRY_SHORT_PAYLOAD_SIZE
    )
    payload = bytearray(payload_size)

    payload[0:4] = (int(time.time()) & 0xFFFFFFFF).to_bytes(4, "big")
    payload[4] = 0
    payload[10] = _u8(cpu_temp_c)

    for i, value in enumerate(tuple(gpu_temps_c)[:5]):
        payload[11 + i] = _u8(value)

    for i, value in enumerate(tuple(fan_rpms)[:20]):
        off = 16 + i * 2
        payload[off : off + 2] = _u16(value)

    if full:
        payload[56] = _u8(cpu_util_pct)
        payload[57:59] = _u16(cpu_clock_mhz)
        # 59..60 CPU power intentionally zero.

        payload[82:84] = _ram_gib(ram_used_gib)
        # 84..88 PSU fields intentionally zero.
        payload[89:91] = _ram_gib(ram_total_gib)
        payload[91:93] = _u16(cpu_clock_max_mhz)
        # 93..94 CPU maximum power intentionally zero.

        for i, gpu in enumerate(tuple(gpu_stats)[:5]):
            cur = 61 + i * 7
            payload[cur] = _u8(_field(gpu, "util_pct"))
            payload[cur + 1 : cur + 3] = _u16(_field(gpu, "clock_mhz"))
            payload[cur + 3 : cur + 5] = _u16(_field(gpu, "power_w"))
            payload[cur + 5 : cur + 7] = _u16(_field(gpu, "mem_used_mib"))

            maximum = 95 + i * 6
            payload[maximum : maximum + 2] = _u16(_field(gpu, "clock_max_mhz"))
            payload[maximum + 2 : maximum + 4] = _u16(_field(gpu, "power_max_w"))
            payload[maximum + 4 : maximum + 6] = _u16(_field(gpu, "mem_total_mib"))

        for i, value in enumerate(tuple(nvme_temps_c)[:5]):
            payload[113 + i] = _u8(value)
        for i, value in enumerate(tuple(sata_temps_c)[:5]):
            payload[118 + i] = _u8(value)

    report = bytearray(REPORT_OUT)
    report[0] = REPORT_ID
    report[1] = SET_HANDSHAKE_DATA
    report[9:11] = payload_size.to_bytes(2, "big")
    report[11 : 11 + payload_size] = payload
    return report


def send_handshake_data(fd, *args, **kwargs):
    """Send one 0x21 report and require NexLinq-style echo acknowledgement."""
    report = build_telemetry_report(*args, **kwargs)
    full = bool(kwargs.get("full", False))
    payload_size = (
        TELEMETRY_FULL_PAYLOAD_SIZE if full else TELEMETRY_SHORT_PAYLOAD_SIZE
    )

    write_report(fd, report)
    reply = wait_for_report(fd, SET_HANDSHAKE_DATA)

    need = 11 + payload_size
    if len(reply) < need:
        raise RuntimeError("Short 0x21 acknowledgement")
    if reply[9:11] != payload_size.to_bytes(2, "big"):
        raise RuntimeError("0x21 acknowledgement length mismatch")
    if reply[11:need] != bytes(report[11:need]):
        raise RuntimeError("0x21 acknowledgement payload mismatch")
    return reply


def build_native_cpu_widget_report(*, graph_style="line", interval_seconds=1):
    """Build the capture-derived native CPU-temperature widget report.

    The line/1-second configuration is physically validated from Linux.
    Bar mode and the allowed interval values are capture/source-confirmed.
    This intentionally remains CPU-temperature-only; arbitrary source
    selectors are not accepted here.
    """
    styles = {"bar": 0x02, "line": 0x03}
    if graph_style not in styles:
        raise ValueError("graph_style must be 'line' or 'bar'")
    if interval_seconds not in (1, 10):
        raise ValueError("Only capture-verified 1 or 10 second intervals are allowed")

    report = bytearray(REPORT_OUT)
    report[0:17] = bytes(
        (
            REPORT_ID,
            ACTIVATE_LAYOUT,
            0x00,
            0x01,
            0x00,
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x02,
            styles[graph_style],
            0x02,
            0x01,
            0x01,
            0x01,
        )
    )
    report[26] = interval_seconds

    label = b"AMD Ryzen 9 9950X"
    report[27] = len(label)
    report[28 : 28 + len(label)] = label
    report[136:144] = b"\xff" * 8
    return report


def send_native_cpu_widget_config(fd, *, graph_style="line", interval_seconds=1):
    """Send the capture-derived CPU widget config and require its 512-byte ACK."""
    report = build_native_cpu_widget_report(
        graph_style=graph_style,
        interval_seconds=interval_seconds,
    )
    write_report(fd, report)
    reply = wait_for_report(fd, ACTIVATE_LAYOUT)

    if len(reply) != REPORT_IN:
        raise RuntimeError(
            f"Unexpected 0x30 acknowledgement length: {len(reply)}/{REPORT_IN}"
        )

    expected = bytearray(report[:REPORT_IN])
    expected[11] = 0x01
    if reply != bytes(expected):
        differences = [
            i
            for i, (actual, wanted) in enumerate(zip(reply, expected))
            if actual != wanted
        ]
        raise RuntimeError(
            "0x30 widget acknowledgement mismatch at byte(s): "
            + ", ".join(map(str, differences[:16]))
        )
    return reply
