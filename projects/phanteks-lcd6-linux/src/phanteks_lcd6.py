#!/usr/bin/env python3
"""Minimal Linux transport for the Phanteks LCD6-HD.

Validated static-image sequence on firmware V1.0.0.10:
    0x22 verify -> 0x2A configure -> 0x28 JPEG pages -> 0x30 activate

This module does not flash firmware, enter a bootloader, or send reset commands.
"""

from __future__ import annotations

import os
import select
import time
from pathlib import Path

VENDOR_ID = "1F3A"
PRODUCT_ID = "6502"

REPORT_ID = 0x01
REPORT_OUT = 1024
REPORT_IN = 512

GET_DEVICE_INFO = 0x22
WRITE_IMAGE = 0x28
SET_LCD_CONFIG = 0x2A
ACTIVATE_LAYOUT = 0x30

BACKGROUND_SLOT = 0xFF
PAYLOAD_PER_PACKET = 1012

# This six-byte prefix is the key detail captured from a successful Windows
# static-image transaction and then validated directly from Linux.
KNOWN_GOOD_ACTIVATE_PREFIX = bytes(
    (REPORT_ID, ACTIVATE_LAYOUT, 0x00, 0x01, 0x00, 0x01)
)


def _hid_id_matches(text: str) -> bool:
    upper = text.upper()
    return f":0000{VENDOR_ID}:0000{PRODUCT_ID}" in upper


def find_lcd_hidraw() -> Path:
    """Return the matching LCD6-HD hidraw node."""
    matches: list[Path] = []

    for node in sorted(Path("/sys/class/hidraw").glob("hidraw*")):
        device = node / "device"
        for candidate in [device, *device.resolve().parents]:
            try:
                if _hid_id_matches((candidate / "uevent").read_text(errors="replace")):
                    matches.append(Path("/dev") / node.name)
                    break
            except (FileNotFoundError, PermissionError, OSError):
                continue

    if not matches:
        raise RuntimeError(
            "No Phanteks LCD6-HD HID interface (1f3a:6502) was found. "
            "Check the USB connection and confirm that lsusb lists the device."
        )

    if len(matches) > 1:
        print(f"Found multiple matching HID interfaces; using {matches[0]}.")

    return matches[0]


def open_lcd(path: Path | None = None) -> tuple[int, Path]:
    """Open the LCD hidraw interface for nonblocking read/write."""
    path = path or find_lcd_hidraw()
    flags = os.O_RDWR | os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC

    try:
        return os.open(path, flags), path
    except PermissionError as exc:
        raise RuntimeError(f"Permission denied opening {path}; run with sudo.") from exc


def write_report(fd: int, report: bytes | bytearray) -> None:
    written = os.write(fd, report)
    if written != len(report):
        raise RuntimeError(f"Short HID write: wrote {written} of {len(report)} bytes")


def wait_for_report(fd: int, command: int, timeout: float = 5.0) -> bytes:
    deadline = time.monotonic() + timeout

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(f"Timed out waiting for command 0x{command:02x} reply")

        readable, _, _ = select.select([fd], [], [], remaining)
        if not readable:
            continue

        data = os.read(fd, REPORT_IN)
        if len(data) >= 2 and data[0] == REPORT_ID and data[1] == command:
            return data


def verify_device(fd: int) -> str:
    """Send the read-only 0x22 query and return the firmware/product string."""
    report = bytearray(REPORT_OUT)
    report[0] = REPORT_ID
    report[1] = GET_DEVICE_INFO
    write_report(fd, report)

    reply = wait_for_report(fd, GET_DEVICE_INFO)
    if len(reply) < 11:
        raise RuntimeError("Device-information reply was too short")

    status = int.from_bytes(reply[6:9], "big")
    payload_length = int.from_bytes(reply[9:11], "big")
    info = (
        reply[11 : 11 + payload_length]
        .decode("utf-8", errors="replace")
        .rstrip("\x00")
    )

    if status != 0 or "LCD6-HD" not in info:
        raise RuntimeError(f"Device verification failed: status={status}, info={info!r}")

    return info


def configure_image_background(fd: int, brightness: int = 70) -> None:
    """Select background-only landscape JPEG mode using command 0x2A."""
    if not 0 <= brightness <= 100:
        raise ValueError("brightness must be between 0 and 100")

    report = bytearray(REPORT_OUT)
    report[0] = REPORT_ID
    report[1] = SET_LCD_CONFIG
    report[9:11] = (9).to_bytes(2, "big")
    report[11] = 0       # layout/mode 0: background only
    report[12] = brightness
    report[13] = 0       # landscape direction
    report[14] = 0       # image background mode
    report[15] = 0       # Celsius, normal layout, display powered on
    report[16:20] = bytes((255, 0, 0, 0))  # ARGB fallback

    write_report(fd, report)
    reply = wait_for_report(fd, SET_LCD_CONFIG)

    if len(reply) < 20:
        raise RuntimeError("LCD-configuration reply was too short")

    if reply != bytes(report[:REPORT_IN]):
        raise RuntimeError(
            "Unexpected LCD-configuration reply: " + reply[:20].hex(" ")
        )

    print("Exact configuration echo received; report accepted.")

    # A successful Windows static-image capture began JPEG transfer roughly
    # 117 ms after the 0x2A acknowledgement. Use a small safety margin.
    time.sleep(0.12)


def upload_background(fd: int, jpeg: bytes, *, timeout: float = 30.0) -> None:
    """Upload a JPEG to background slot 0xFF with per-page acknowledgements."""
    if not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9"):
        raise ValueError("Input does not appear to be a complete JPEG")

    pages = (len(jpeg) + PAYLOAD_PER_PACKET - 1) // PAYLOAD_PER_PACKET
    print(f"Uploading {len(jpeg):,} bytes in {pages} acknowledged packets...")

    deadline = time.monotonic() + timeout
    last_bucket = -1

    for page in range(pages):
        chunk = jpeg[page * PAYLOAD_PER_PACKET : (page + 1) * PAYLOAD_PER_PACKET]

        report = bytearray(REPORT_OUT)
        report[0] = REPORT_ID
        report[1] = WRITE_IMAGE
        report[2:6] = len(jpeg).to_bytes(4, "big")
        report[6:9] = page.to_bytes(3, "big")
        report[9:11] = (len(chunk) + 1).to_bytes(2, "big")
        report[11] = BACKGROUND_SLOT
        report[12 : 12 + len(chunk)] = chunk

        write_report(fd, report)

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("Image upload exceeded its transaction deadline")

        reply = wait_for_report(fd, WRITE_IMAGE, timeout=min(1.0, remaining))
        if len(reply) < 12:
            raise RuntimeError(f"Short image acknowledgement for packet {page + 1}")

        acknowledged_page = int.from_bytes(reply[6:9], "big")
        if acknowledged_page != page:
            raise RuntimeError(
                f"Unexpected image acknowledgement: sent page {page}, "
                f"device acknowledged {acknowledged_page}"
            )

        if page == 0:
            print("First image packet received a matching page acknowledgement.")

        percent = ((page + 1) * 100) // pages
        bucket = percent // 10
        if bucket > last_bucket or page + 1 == pages:
            print(f"  {percent:3d}% ({page + 1}/{pages})")
            last_bucket = bucket


def activate_background(fd: int) -> None:
    """Activate the uploaded background and require the observed success ACK."""
    report = bytearray(REPORT_OUT)
    report[: len(KNOWN_GOOD_ACTIVATE_PREFIX)] = KNOWN_GOOD_ACTIVATE_PREFIX
    write_report(fd, report)

    reply = wait_for_report(fd, ACTIVATE_LAYOUT)
    if len(reply) < 12:
        raise RuntimeError("Layout-activation reply was too short")
    if reply[11] != 0x01:
        raise RuntimeError(
            "Unexpected 0x30 activation status: " + reply[:16].hex(" ")
        )


def show_jpeg(jpeg: bytes, *, brightness: int = 70) -> str:
    """Run the complete validated static-image sequence in one HID session."""
    fd, path = open_lcd()
    print(f"Using {path}")

    try:
        info = verify_device(fd)
        print(f"Verified: {info}")

        print("1/3 Configuring background-only landscape mode...")
        configure_image_background(fd, brightness=brightness)

        print("2/3 Uploading JPEG...")
        upload_background(fd, jpeg)

        # Successful Windows sequencing waited about 105 ms before 0x30.
        time.sleep(0.10)

        print("3/3 Sending validated layout activation (0x30)...")
        activate_background(fd)
    finally:
        os.close(fd)

    print("Complete sequence sent in one uninterrupted HID session.")
    return info
