"""
Hardware diagnostic tests for the DS18B20 temperature sensor and heater relay.

Run on the Raspberry Pi:
    sudo python3 tests/test_hardware.py

Tests:
    1. DS18B20 detection and reading
    2. Relay toggle (GPIO 26)
    3. Heater + sensor integration (relay ON → temp should rise)
"""

import sys
import os
import time
import glob

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_separator(name):
    print()
    print("=" * 60)
    print(f"  TEST: {name}")
    print("=" * 60)
    print()


def test_ds18b20_detection():
    """Test 1: Can we find the DS18B20 on the 1-Wire bus?"""
    test_separator("DS18B20 Detection")

    W1_PATH = "/sys/bus/w1/devices/"
    devices = glob.glob(os.path.join(W1_PATH, "28-*"))

    if not devices:
        print("[FAIL] No DS18B20 sensor found!")
        print()
        print("  Checklist:")
        print("  [ ] Is 1-Wire enabled?  Check: grep dtoverlay /boot/config.txt")
        print("  [ ] Did you reboot after enabling 1-Wire?")
        print("  [ ] Is the DQ pin connected to GPIO 4?")
        print("  [ ] Is there a 4.7kΩ pull-up resistor between DQ and VCC?")
        print("  [ ] Are w1 kernel modules loaded?  Check: lsmod | grep w1")
        return False

    for device in devices:
        device_id = os.path.basename(device)
        print(f"[OK] Found sensor: {device_id}")

        slave_file = os.path.join(device, "w1_slave")
        try:
            with open(slave_file, 'r') as f:
                lines = f.readlines()

            print(f"  Raw output:")
            for line in lines:
                print(f"    {line.strip()}")

            if "YES" in lines[0]:
                print(f"  [OK] CRC check: PASSED")
            else:
                print(f"  [FAIL] CRC check: FAILED — bad wiring or sensor issue")
                return False

            temp_pos = lines[1].find("t=")
            if temp_pos != -1:
                temp = float(lines[1][temp_pos + 2:]) / 1000.0
                print(f"  [OK] Temperature: {temp}°C")

                if -10 < temp < 80:
                    print(f"  [OK] Value looks reasonable ✓")
                else:
                    print(f"  [WARN] Value seems unusual — double-check sensor")
            else:
                print(f"  [FAIL] Could not parse temperature from output")
                return False

        except Exception as e:
            print(f"  [FAIL] Error reading sensor: {e}")
            return False

    return True


def test_ds18b20_stability():
    """Test 2: Take 5 readings and check stability."""
    test_separator("DS18B20 Stability (5 readings)")

    try:
        from src.temperature import TemperatureSensor
        sensor = TemperatureSensor()

        if sensor.device_path is None:
            print("[FAIL] Sensor not initialised — see detection test above")
            return False

        readings = []
        for i in range(5):
            temp = sensor.read_temperature()
            if temp is not None:
                readings.append(temp)
                print(f"  Reading {i+1}: {temp}°C")
            else:
                print(f"  Reading {i+1}: FAILED")
            time.sleep(1)

        if len(readings) < 3:
            print(f"[FAIL] Too many failed readings ({5 - len(readings)}/5)")
            return False

        spread = max(readings) - min(readings)
        avg = sum(readings) / len(readings)
        print()
        print(f"  Average:  {avg:.1f}°C")
        print(f"  Spread:   {spread:.1f}°C")

        if spread < 2.0:
            print(f"  [OK] Readings are stable ✓")
        else:
            print(f"  [WARN] Readings vary a lot — check wiring / pull-up resistor")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_relay_toggle():
    """Test 3: Toggle the relay on GPIO 26 — listen for a click."""
    test_separator("Relay Toggle (GPIO 26)")

    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("[FAIL] RPi.GPIO not installed!")
        print("  Fix: pip install RPi.GPIO")
        return False

    PIN = int(os.getenv("HEATER_RELAY_PIN", "26"))
    active_low = os.getenv("HEATER_RELAY_ACTIVE_LOW", "true").lower() in ("true", "1", "yes")

    print(f"  Relay pin: GPIO {PIN}")
    print(f"  Active-LOW: {active_low}")
    print()

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN, GPIO.OUT)

        # Start OFF
        GPIO.output(PIN, GPIO.HIGH if active_low else GPIO.LOW)
        print("  [1/4] Relay OFF — you should hear nothing")
        time.sleep(1)

        # Turn ON
        GPIO.output(PIN, GPIO.LOW if active_low else GPIO.HIGH)
        print("  [2/4] Relay ON  — you should hear a CLICK ✓")
        time.sleep(2)

        # Turn OFF
        GPIO.output(PIN, GPIO.HIGH if active_low else GPIO.LOW)
        print("  [3/4] Relay OFF — you should hear another CLICK ✓")
        time.sleep(1)

        # One more cycle
        GPIO.output(PIN, GPIO.LOW if active_low else GPIO.HIGH)
        print("  [4/4] Relay ON  — CLICK")
        time.sleep(1)
        GPIO.output(PIN, GPIO.HIGH if active_low else GPIO.LOW)
        print("         Relay OFF — CLICK")
        time.sleep(0.5)

        GPIO.cleanup(PIN)

        print()
        answer = input("  Did you hear the relay clicking? (y/n): ").strip().lower()
        if answer == 'y':
            print("  [OK] Relay is working ✓")
            return True
        else:
            print("  [FAIL] Relay did not click!")
            print()
            print("  Checklist:")
            print("  [ ] Is IN1 connected to GPIO 26 (pin 37)?")
            print("  [ ] Is VCC connected to 5V?")
            print("  [ ] Is GND connected?")
            print("  [ ] Try setting HEATER_RELAY_ACTIVE_LOW=false")
            return False

    except Exception as e:
        print(f"[FAIL] GPIO error: {e}")
        print("  Make sure you're running with sudo!")
        try:
            GPIO.cleanup(PIN)
        except Exception:
            pass
        return False


def test_heater_warms():
    """Test 4: Turn heater ON for 30s and check if temperature rises."""
    test_separator("Heater Integration (30s warm-up test)")

    try:
        import RPi.GPIO as GPIO
        from src.temperature import TemperatureSensor
    except ImportError as e:
        print(f"[FAIL] Missing module: {e}")
        return False

    PIN = int(os.getenv("HEATER_RELAY_PIN", "26"))
    active_low = os.getenv("HEATER_RELAY_ACTIVE_LOW", "true").lower() in ("true", "1", "yes")

    sensor = TemperatureSensor()
    if sensor.device_path is None:
        print("[FAIL] Temperature sensor not available")
        return False

    start_temp = sensor.read_temperature()
    if start_temp is None:
        print("[FAIL] Could not read starting temperature")
        return False

    print(f"  Starting temperature: {start_temp}°C")
    print(f"  Turning heater ON for 30 seconds...")
    print()

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN, GPIO.OUT)

        # Heater ON
        GPIO.output(PIN, GPIO.LOW if active_low else GPIO.HIGH)

        for i in range(6):
            time.sleep(5)
            temp = sensor.read_temperature()
            elapsed = (i + 1) * 5
            if temp is not None:
                delta = temp - start_temp
                bar = "█" * int(max(0, delta) * 5)
                print(f"  {elapsed:2d}s — {temp}°C  (Δ{delta:+.1f}°C) {bar}")
            else:
                print(f"  {elapsed:2d}s — reading failed")

        # Heater OFF
        GPIO.output(PIN, GPIO.HIGH if active_low else GPIO.LOW)
        print()
        print("  Heater OFF.")

        end_temp = sensor.read_temperature()
        if end_temp is not None:
            total_delta = end_temp - start_temp
            print(f"  Final temperature: {end_temp}°C  (Δ{total_delta:+.1f}°C)")
            print()

            if total_delta > 0.5:
                print(f"  [OK] Temperature rose by {total_delta:.1f}°C — heater is working ✓")
                return True
            elif total_delta > 0:
                print(f"  [WARN] Small rise ({total_delta:.1f}°C) — might need more time or better contact")
                return True
            else:
                print(f"  [FAIL] Temperature didn't rise — check heating pad connection to relay")
                return False
        else:
            print("  [FAIL] Could not read final temperature")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    finally:
        try:
            GPIO.output(PIN, GPIO.HIGH if active_low else GPIO.LOW)
            GPIO.cleanup(PIN)
        except Exception:
            pass


def main():
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       Panopticon — Hardware Diagnostics                   ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print("  This script tests the DS18B20 sensor and heater relay.")
    print("  Run with: sudo python3 tests/test_hardware.py")
    print()

    results = {}

    # Test 1: DS18B20 detection
    results["DS18B20 Detection"] = test_ds18b20_detection()

    # Test 2: DS18B20 stability (only if detection passed)
    if results["DS18B20 Detection"]:
        results["DS18B20 Stability"] = test_ds18b20_stability()
    else:
        results["DS18B20 Stability"] = None

    # Test 3: Relay toggle
    results["Relay Toggle"] = test_relay_toggle()

    # Test 4: Integration test (only if both sensor and relay work)
    if results["DS18B20 Detection"] and results["Relay Toggle"]:
        print()
        answer = input("Run 30-second heater warm-up test? (y/n): ").strip().lower()
        if answer == 'y':
            results["Heater Integration"] = test_heater_warms()
        else:
            results["Heater Integration"] = None
            print("  Skipped.")
    else:
        results["Heater Integration"] = None

    # Summary
    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print()

    for test_name, passed in results.items():
        if passed is True:
            status = "✅ PASS"
        elif passed is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"  {status}  {test_name}")

    print()

    if all(v is True for v in results.values() if v is not None):
        print("  All tests passed! 🎉")
    else:
        print("  Some tests failed — check the output above for details.")

    print()


if __name__ == "__main__":
    main()
