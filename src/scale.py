"""
Scale module for Panopticon Raspberry.
Reads weight from an HX711 load cell amplifier and logs it to Appwrite.

=====================================================================
 IMPORTANT — BEFORE FIRST USE:
=====================================================================

 1. Install the hx711py library on the Raspberry Pi:
      sudo apt-get install git
      sudo git clone https://github.com/j-dohnalek/hx711py
      cd hx711py
      sudo python3 setup.py install

 2. Wire the HX711 module:
      HX711 VCC  → Raspberry Pi 3.3V or 5V
      HX711 GND  → Raspberry Pi GND
      HX711 DT   → GPIO 5  (configurable via HX711_DT_PIN env var)
      HX711 SCK  → GPIO 6  (configurable via HX711_SCK_PIN env var)

 3. Calibrate the scale (REQUIRED before meaningful readings):
      sudo python3 -m src.scale_calibration

    This interactive wizard will:
      a) Read the empty scale to determine the OFFSET
      b) Ask you to place a known weight to calculate the RATIO
      c) Verify the calibration with test readings
      d) Save values to scale_calibration.json

    Without calibration, the scale will use default values
    (offset=0, ratio=1) and readings will be raw/meaningless.

 4. Run the scale module:
      sudo python3 -m src.scale           # standalone
      sudo python3 -m src.start_aw        # starts with all modules

=====================================================================
"""

import time
import os
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [Scale] %(message)s')

# --- Configuration ---
# GPIO pins for HX711 (BCM numbering)
# Override via environment variables if needed
DT_PIN = int(os.getenv("HX711_DT_PIN", "5"))   # Data pin (DOUT)
SCK_PIN = int(os.getenv("HX711_SCK_PIN", "6"))  # Clock pin (SCK)

# Calibration values — run scale_calibration.py to determine these
# Store them in .env or calibration.json for persistence
CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scale_calibration.json")

DEFAULT_OFFSET = 0
DEFAULT_RATIO = 1  # raw_value / grams

# How often to read the scale (seconds)
READ_INTERVAL = float(os.getenv("SCALE_READ_INTERVAL", "2.0"))

# --- Coffee State Machine ---
# Minimum weight to consider a cup with coffee is present
COFFEE_THRESHOLD = float(os.getenv("SCALE_COFFEE_THRESHOLD", "150.0"))  # grams

# Weight below this = cup removed / scale empty
CUP_REMOVE_THRESHOLD = float(os.getenv("SCALE_CUP_REMOVE_THRESHOLD", "50.0"))  # grams

# Weight drop (grams) over one read cycle to consider active drinking
DRINKING_DROP_THRESHOLD = float(os.getenv("SCALE_DRINKING_DROP_THRESHOLD", "10.0"))  # grams


# Shared weight file — other modules (e.g. heater.py) can read the latest weight
WEIGHT_FILE = "/tmp/panopticon_weight.json"


class Scale:
    """Reads weight from HX711 load cell and reports changes."""

    def __init__(self, dt_pin=DT_PIN, sck_pin=SCK_PIN):
        self.dt_pin = dt_pin
        self.sck_pin = sck_pin
        self.hx = None
        self.offset = DEFAULT_OFFSET
        self.ratio = DEFAULT_RATIO
        self.last_weight = 0.0
        self.last_report_time = 0

        self._load_calibration()
        self._init_hx711()

    def _load_calibration(self):
        """Load calibration values from file or env."""
        # Try environment variables first
        env_offset = os.getenv("HX711_OFFSET")
        env_ratio = os.getenv("HX711_RATIO")

        if env_offset and env_ratio:
            self.offset = float(env_offset)
            self.ratio = float(env_ratio)
            logging.info(f"Calibration from env: offset={self.offset}, ratio={self.ratio}")
            return

        # Try calibration file
        if os.path.exists(CALIBRATION_FILE):
            try:
                with open(CALIBRATION_FILE, 'r') as f:
                    cal = json.load(f)
                self.offset = cal.get("offset", DEFAULT_OFFSET)
                self.ratio = cal.get("ratio", DEFAULT_RATIO)
                logging.info(f"Calibration loaded from {CALIBRATION_FILE}: offset={self.offset}, ratio={self.ratio}")
                return
            except Exception as e:
                logging.warning(f"Failed to load calibration file: {e}")

        logging.warning(
            "No calibration found! Using defaults. "
            "Run 'python -m src.scale_calibration' first."
        )

    def _init_hx711(self):
        """Initialize the HX711 sensor."""
        try:
            # hx711py is cloned as a sibling directory, not pip-installed
            import sys
            hx711_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hx711py")
            if hx711_path not in sys.path:
                sys.path.insert(0, hx711_path)

            from hx711 import HX711
            self.hx = HX711(self.dt_pin, self.sck_pin)
            self.hx.set_offset(self.offset)
            self.hx.set_scale(self.ratio)
            logging.info(f"HX711 initialized on DT={self.dt_pin}, SCK={self.sck_pin}")
        except ImportError:
            logging.error(
                "hx711 module not found! "
                "Clone it with: git clone https://github.com/j-dohnalek/hx711py"
            )
            self.hx = None
        except Exception as e:
            logging.error(f"Failed to initialize HX711: {e}")
            self.hx = None

    def read_weight(self, num_readings=5):
        """
        Read weight from the scale.
        Takes multiple readings and returns the median for stability.

        Returns:
            float: Weight in grams, or None if reading failed.
        """
        if self.hx is None:
            return None

        try:
            # Take multiple readings for accuracy
            readings = []
            for _ in range(num_readings):
                val = self.hx.get_grams()
                if val is not None:
                    readings.append(val)

            if not readings:
                return None

            # Use median to filter outliers
            readings.sort()
            median = readings[len(readings) // 2]
            return round(median, 1)

        except Exception as e:
            logging.error(f"Error reading scale: {e}")
            return None

    def tare(self):
        """Zero the scale (set current weight as zero point)."""
        if self.hx is None:
            logging.error("Cannot tare: HX711 not initialized")
            return False

        try:
            self.hx.tare()
            logging.info("Scale tared (zeroed)")
            return True
        except Exception as e:
            logging.error(f"Tare failed: {e}")
            return False

    def start(self, callback=None):
        """
        Main loop: coffee state machine.
        Detects when a coffee is placed, being drunk, and removed.
        Only fires callback on meaningful state transitions — not on every reading.

        Args:
            callback: Optional function(coffee_event_dict) called on coffee events.
                      Event types: 'coffee_detected', 'coffee_drinking', 'coffee_done'
        """
        if self.hx is None:
            logging.error("Cannot start: HX711 not initialized.")
            logging.error("Make sure the hx711py library is installed and wiring is correct.")
            return

        logging.info("Scale reader started (coffee state machine).")
        logging.info(f"  Read interval: {READ_INTERVAL}s")
        logging.info(f"  Coffee threshold: {COFFEE_THRESHOLD}g")
        logging.info(f"  Cup remove threshold: {CUP_REMOVE_THRESHOLD}g")
        logging.info(f"  Drinking drop threshold: {DRINKING_DROP_THRESHOLD}g per cycle")

        # States: 'empty', 'coffee_present'
        state = 'empty'
        prev_weight = 0.0

        try:
            while True:
                weight = self.read_weight()

                if weight is None:
                    time.sleep(READ_INTERVAL)
                    continue

                # Write latest weight to shared file for heater.py
                try:
                    with open(WEIGHT_FILE, 'w') as f:
                        json.dump({
                            "weight": weight,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }, f)
                except Exception:
                    pass  # Non-critical

                now_iso = datetime.now(timezone.utc).isoformat()

                if state == 'empty':
                    # Transition: cup with coffee placed
                    if weight >= COFFEE_THRESHOLD:
                        state = 'coffee_present'
                        logging.info(f"☕ Coffee detected! Weight: {weight}g")
                        if callback:
                            callback({
                                "event": "coffee_detected",
                                "timestamp": now_iso,
                                "weight": weight,
                                "unit": "g",
                            })

                elif state == 'coffee_present':
                    # Transition: cup removed
                    if weight < CUP_REMOVE_THRESHOLD:
                        state = 'empty'
                        logging.info(f"✅ Coffee done. Weight dropped to {weight}g")
                        if callback:
                            callback({
                                "event": "coffee_done",
                                "timestamp": now_iso,
                                "weight": weight,
                                "unit": "g",
                            })

                    # Active drinking: weight dropping significantly each cycle
                    elif (prev_weight - weight) >= DRINKING_DROP_THRESHOLD:
                        logging.info(f"🫗 Drinking detected: {prev_weight}g → {weight}g")
                        if callback:
                            callback({
                                "event": "coffee_drinking",
                                "timestamp": now_iso,
                                "weight": weight,
                                "unit": "g",
                            })

                prev_weight = weight
                time.sleep(READ_INTERVAL)

        except KeyboardInterrupt:
            logging.info("Scale reader stopped.")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up GPIO resources."""
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logging.info("GPIO cleaned up")
        except Exception:
            pass


def main():
    """Entry point when run as a module."""
    from src.db_connector import DatabaseConnector

    db = DatabaseConnector()
    scale = Scale()

    def on_coffee_event(data):
        """Callback when a coffee state transition is detected."""
        logging.info(f"Coffee event: {data['event']} @ {data.get('weight', '?')}g")
        db.send_coffee_event(data)

    scale.start(callback=on_coffee_event)


if __name__ == "__main__":
    main()
