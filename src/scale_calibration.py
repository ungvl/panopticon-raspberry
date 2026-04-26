"""
Interactive calibration script for the HX711 scale.

This script helps you determine the offset and ratio values
needed for accurate weight readings.

Usage:
    sudo python3 -m src.scale_calibration

Steps:
    1. Remove everything from the scale
    2. Script reads the raw offset value
    3. Place a known weight on the scale
    4. Script calculates the ratio
    5. Values are saved to scale_calibration.json
"""

import os
import sys
import json
import time

# GPIO pins — match these to your wiring
DT_PIN = int(os.getenv("HX711_DT_PIN", "5"))
SCK_PIN = int(os.getenv("HX711_SCK_PIN", "6"))

CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scale_calibration.json")


def get_raw_readings(hx, num_readings=20):
    """Take multiple raw readings and return their average."""
    readings = []
    for i in range(num_readings):
        val = hx.get_grams()
        if val is not None:
            readings.append(val)
        time.sleep(0.1)

    if not readings:
        return None

    readings.sort()
    # Remove top and bottom 10% outliers
    trim = max(1, len(readings) // 10)
    trimmed = readings[trim:-trim] if len(readings) > 4 else readings
    return sum(trimmed) / len(trimmed)


def main():
    print("=" * 60)
    print("  HX711 Scale Calibration")
    print("  Panopticon Raspberry")
    print("=" * 60)
    print()
    print(f"  DT Pin (DOUT): GPIO {DT_PIN}")
    print(f"  SCK Pin:       GPIO {SCK_PIN}")
    print(f"  Output file:   {CALIBRATION_FILE}")
    print()

    try:
        # hx711py is cloned as a sibling directory, not pip-installed
        hx711_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hx711py")
        if hx711_path not in sys.path:
            sys.path.insert(0, hx711_path)

        from hx711 import HX711
    except ImportError:
        print("[ERROR] hx711 module not found!")
        print("Clone it with:")
        print("  git clone https://github.com/j-dohnalek/hx711py")
        sys.exit(1)

    # Initialize
    print("[INFO] Initializing HX711...")
    try:
        hx = HX711(DT_PIN, SCK_PIN)
    except Exception as e:
        print(f"[ERROR] Failed to initialize HX711: {e}")
        print("Check your wiring and make sure you're running with sudo.")
        sys.exit(1)

    # --- Step 1: Determine Offset ---
    print()
    print("-" * 40)
    print("STEP 1: Determine the Offset")
    print("-" * 40)
    print()
    input("Remove ALL weight from the scale, then press ENTER...")
    print()
    print("[INFO] Reading empty scale (this takes a few seconds)...")

    # Reset scale to no offset/ratio
    hx.set_offset(0)
    hx.set_scale(1)

    offset = get_raw_readings(hx)
    if offset is None:
        print("[ERROR] Could not read from the scale. Check wiring!")
        sys.exit(1)

    print(f"[OK] Offset (empty scale raw value): {offset:.2f}")
    hx.set_offset(offset)

    # --- Step 2: Determine Ratio ---
    print()
    print("-" * 40)
    print("STEP 2: Determine the Ratio")
    print("-" * 40)
    print()

    while True:
        try:
            known_weight = float(input("Enter the weight of your known object (in grams): "))
            if known_weight <= 0:
                print("Weight must be a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    print()
    input(f"Place the {known_weight}g object on the scale, then press ENTER...")
    print()
    print("[INFO] Reading scale with known weight...")

    raw_with_weight = get_raw_readings(hx)
    if raw_with_weight is None:
        print("[ERROR] Could not read from the scale. Check wiring!")
        sys.exit(1)

    # ratio = (raw_reading - offset) / known_weight
    ratio = (raw_with_weight - offset) / known_weight if known_weight != 0 else 1
    
    print(f"[OK] Raw reading with weight: {raw_with_weight:.2f}")
    print(f"[OK] Calculated ratio: {ratio:.6f}")

    # --- Step 3: Verify ---
    print()
    print("-" * 40)
    print("STEP 3: Verify")
    print("-" * 40)
    print()

    hx.set_scale(ratio)
    print("[INFO] Verifying calibration (reading 5 times)...")
    print()

    for i in range(5):
        weight = hx.get_grams()
        print(f"  Reading {i+1}: {weight:.1f} g")
        time.sleep(0.5)

    print()
    print(f"  Expected: {known_weight} g")

    # --- Step 4: Save ---
    print()
    save = input("Save calibration values? (y/n): ").strip().lower()

    if save == 'y':
        cal_data = {
            "offset": offset,
            "ratio": ratio,
            "known_weight_used": known_weight,
            "calibrated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "dt_pin": DT_PIN,
            "sck_pin": SCK_PIN,
        }

        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(cal_data, f, indent=2)

        print(f"[OK] Calibration saved to {CALIBRATION_FILE}")
        print()
        print("You can also add these to your .env file:")
        print(f"  HX711_OFFSET={offset}")
        print(f"  HX711_RATIO={ratio}")
    else:
        print("[INFO] Calibration NOT saved.")

    print()
    print("=" * 60)
    print("  Calibration complete!")
    print("=" * 60)

    # Cleanup
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
    except Exception:
        pass


if __name__ == "__main__":
    main()
