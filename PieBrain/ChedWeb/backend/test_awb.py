#!/usr/bin/env python3
"""Test script to determine available AWB modes."""

try:
    from picamera2 import Picamera2
    import libcamera

    print("Testing AWB Mode Enums:")
    print("-" * 50)

    # Try to list all attributes of AwbModeEnum
    awb_enum = libcamera.controls.AwbModeEnum
    print(f"\nAwbModeEnum attributes:")
    for attr in dir(awb_enum):
        if not attr.startswith("_"):
            try:
                value = getattr(awb_enum, attr)
                print(f"  {attr}: {value}")
            except Exception as e:
                print(f"  {attr}: ERROR - {e}")

    # Also check the picamera2 camera controls
    picam2 = Picamera2()
    if "AwbMode" in picam2.camera_controls:
        print(f"\nCamera AwbMode control: {picam2.camera_controls['AwbMode']}")

    picam2.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
