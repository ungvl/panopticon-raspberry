"""
Heater module for Panopticon Raspberry.
Controls a relay-driven heating pad based on scale weight and temperature.

=====================================================================
 HARDWARE:
=====================================================================

  Relay Module:
    IN1  → GPIO 26 (BCM), pin 37
    VCC  → Raspberry Pi 5V
    GND  → Raspberry Pi GND

  Heating Pad:
    Fyearfly 12V / 12W constant temperature heating plate (100x120mm)
    Max temperature: 60°C
    Connected via the relay's NO (Normally Open) terminal

  Temperature Sensor:
    DS18B20 on GPIO 4 (via 1-Wire — see temperature.py)

  Scale:
    HX711 on GPIO 5/6 (via scale.py — weight shared via /tmp file)

=====================================================================
 LOGIC:
=====================================================================

  1. Scale detects cup (weight > 50g)  →  heater ENABLED
  2. Temperature < 58°C               →  relay ON  (heating)
  3. Temperature ≥ 60°C               →  relay OFF (target reached)
  4. Cup removed (weight < 50g)        →  relay OFF immediately

  Hysteresis prevents rapid on/off cycling near the target temp.

=====================================================================
"""

import time
import os
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [Heater] %(message)s')

# --- Configuration ---
# Relay GPIO pin (BCM numbering)
RELAY_PIN = int(os.getenv("HEATER_RELAY_PIN", "26"))

# Relay is active-LOW by default (most relay modules: LOW = ON)
ACTIVE_LOW = os.getenv("HEATER_RELAY_ACTIVE_LOW", "true").lower() in ("true", "1", "yes")

# Target temperature in °C
TARGET_TEMP = float(os.getenv("HEATER_TARGET_TEMP", "60.0"))

# Hysteresis in °C (heater turns ON at target - hysteresis)
HYSTERESIS = float(os.getenv("HEATER_HYSTERESIS", "2.0"))

# Weight threshold (grams) to consider a cup is on the scale
CUP_THRESHOLD = float(os.getenv("HEATER_CUP_THRESHOLD", "50.0"))

# How often to check conditions (seconds)
CHECK_INTERVAL = float(os.getenv("HEATER_CHECK_INTERVAL", "2.0"))

# Max age of weight data before considering it stale (seconds)
WEIGHT_MAX_AGE = float(os.getenv("HEATER_WEIGHT_MAX_AGE", "10.0"))

# Shared weight file (written by scale.py)
WEIGHT_FILE = "/tmp/panopticon_weight.json"


class Heater:
    """Controls a relay-driven heater based on scale weight and temperature readings."""

    def __init__(self):
        self.gpio_available = False
        self.heater_on = False
        self.temp_sensor = None

        self._init_gpio()
        self._init_temperature()

    def _init_gpio(self):
        """Initialize GPIO for relay control."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(RELAY_PIN, GPIO.OUT)

            # Start with heater OFF
            self._set_relay(False)
            self.gpio_available = True
            logging.info(f"GPIO initialized: relay on pin {RELAY_PIN} (active-{'LOW' if ACTIVE_LOW else 'HIGH'})")

        except ImportError:
            logging.error(
                "RPi.GPIO module not found! "
                "Install with: pip install RPi.GPIO"
            )
        except Exception as e:
            logging.error(f"Failed to initialize GPIO: {e}")

    def _init_temperature(self):
        """Initialize the temperature sensor for direct readings."""
        try:
            from src.temperature import TemperatureSensor
            self.temp_sensor = TemperatureSensor()
            if self.temp_sensor.device_path is None:
                logging.warning("Temperature sensor not found — heater will not activate")
                self.temp_sensor = None
        except Exception as e:
            logging.error(f"Failed to initialize temperature sensor: {e}")
            self.temp_sensor = None

    def _set_relay(self, on):
        """
        Set the relay state.

        Args:
            on: True = heater ON, False = heater OFF
        """
        if not self.gpio_available:
            return

        try:
            import RPi.GPIO as GPIO

            if ACTIVE_LOW:
                # Active-LOW: LOW = relay ON, HIGH = relay OFF
                GPIO.output(RELAY_PIN, GPIO.LOW if on else GPIO.HIGH)
            else:
                # Active-HIGH: HIGH = relay ON, LOW = relay OFF
                GPIO.output(RELAY_PIN, GPIO.HIGH if on else GPIO.LOW)

            if on != self.heater_on:
                self.heater_on = on
                state_str = "ON 🔥" if on else "OFF ❄️"
                logging.info(f"Heater {state_str}")

        except Exception as e:
            logging.error(f"Failed to set relay: {e}")

    def _read_weight(self):
        """
        Read the latest weight from the shared file written by scale.py.

        Returns:
            float: Weight in grams, or None if unavailable/stale.
        """
        try:
            if not os.path.exists(WEIGHT_FILE):
                return None

            with open(WEIGHT_FILE, 'r') as f:
                data = json.load(f)

            weight = data.get("weight")
            timestamp = data.get("timestamp")

            if weight is None or timestamp is None:
                return None

            # Check if data is stale
            data_time = datetime.fromisoformat(timestamp)
            age = (datetime.now(timezone.utc) - data_time).total_seconds()

            if age > WEIGHT_MAX_AGE:
                return None

            return float(weight)

        except (json.JSONDecodeError, ValueError, OSError) as e:
            logging.debug(f"Could not read weight file: {e}")
            return None

    def _read_temperature(self):
        """
        Read the current temperature from the DS18B20.

        Returns:
            float: Temperature in °C, or None if unavailable.
        """
        if self.temp_sensor is None:
            return None

        return self.temp_sensor.read_temperature()

    def start(self, callback=None):
        """
        Main loop: monitor weight and temperature, control heater.

        Args:
            callback: Optional function(heater_data_dict) called on state changes.
        """
        if not self.gpio_available:
            logging.error("Cannot start: GPIO not available.")
            return

        if self.temp_sensor is None:
            logging.error("Cannot start: Temperature sensor not available.")
            return

        logging.info("Heater controller started.")
        logging.info(f"  Relay pin: GPIO {RELAY_PIN}")
        logging.info(f"  Target temp: {TARGET_TEMP}°C (hysteresis: ±{HYSTERESIS}°C)")
        logging.info(f"  Cup threshold: {CUP_THRESHOLD}g")
        logging.info(f"  Check interval: {CHECK_INTERVAL}s")

        last_state = None  # Track state changes for callbacks

        try:
            while True:
                weight = self._read_weight()
                temp = self._read_temperature()

                cup_present = weight is not None and weight >= CUP_THRESHOLD

                if not cup_present:
                    # No cup → heater OFF (safety)
                    if self.heater_on:
                        reason = "no weight data" if weight is None else f"cup removed ({weight:.0f}g)"
                        logging.info(f"Heater OFF — {reason}")
                    self._set_relay(False)

                elif temp is not None:
                    # Cup present + temperature available → thermostat logic
                    if self.heater_on:
                        # Currently heating — turn OFF when target reached
                        if temp >= TARGET_TEMP:
                            logging.info(f"Target reached: {temp}°C ≥ {TARGET_TEMP}°C")
                            self._set_relay(False)
                    else:
                        # Currently OFF — turn ON when below threshold
                        if temp < (TARGET_TEMP - HYSTERESIS):
                            logging.info(f"Heating needed: {temp}°C < {TARGET_TEMP - HYSTERESIS}°C")
                            self._set_relay(True)

                else:
                    # Cup present but no temperature reading — safety OFF
                    if self.heater_on:
                        logging.warning("No temperature reading — heater OFF for safety")
                        self._set_relay(False)

                # Fire callback on state changes
                current_state = self.heater_on
                if callback and current_state != last_state:
                    data = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "state": "on" if current_state else "off",
                        "temperature": temp,
                        "weight": weight,
                        "target_temp": TARGET_TEMP,
                    }
                    callback(data)
                    last_state = current_state

                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logging.info("Heater controller stopped.")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up GPIO — ensure heater is OFF."""
        logging.info("Shutting down heater — turning OFF for safety")
        self._set_relay(False)

        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup(RELAY_PIN)
            logging.info("GPIO cleaned up")
        except Exception:
            pass


def main():
    """Entry point when run as a module."""
    from src.db_connector import DatabaseConnector

    db = DatabaseConnector()
    heater = Heater()

    def on_state_change(data):
        """Callback when heater state changes."""
        logging.info(f"Sending heater data: state={data['state']}, temp={data.get('temperature')}°C")
        db.send_heater_data(data)

    heater.start(callback=on_state_change)


if __name__ == "__main__":
    main()
