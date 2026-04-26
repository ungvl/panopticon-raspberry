"""
DS18B20 Temperature Sensor module for Panopticon Raspberry.
Reads temperature from a DS18B20 sensor via the 1-Wire interface and logs it.

=====================================================================
 IMPORTANT — BEFORE FIRST USE:
=====================================================================

 1. Enable the 1-Wire interface on the Raspberry Pi:
      sudo raspi-config  → Interface Options → 1-Wire → Enable

    Or manually add to /boot/config.txt:
      dtoverlay=w1-gpio,gpiopin=4

    Then reboot.

 2. Wire the DS18B20:
      DS18B20 VCC (red)   → Raspberry Pi 3.3V
      DS18B20 GND (black) → Raspberry Pi GND
      DS18B20 DQ  (yellow)→ GPIO 4  (pin 7)

    IMPORTANT: A 4.7kΩ pull-up resistor is required between DQ and VCC.

 3. Verify the sensor is detected:
      ls /sys/bus/w1/devices/28-*
      cat /sys/bus/w1/devices/28-*/w1_slave

 4. Run the temperature module:
      sudo python3 -m src.temperature       # standalone
      sudo python3 -m src.start_aw          # starts with all modules

=====================================================================
"""

import time
import os
import glob
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [Temp] %(message)s')

# --- Configuration ---
# 1-Wire device base path
W1_DEVICES_PATH = "/sys/bus/w1/devices/"
W1_DEVICE_PREFIX = "28-"  # DS18B20 devices start with 28-

# How often to read the sensor (seconds)
READ_INTERVAL = float(os.getenv("TEMP_READ_INTERVAL", "2.0"))

# Minimum temperature change (°C) to trigger a new log entry
CHANGE_THRESHOLD = float(os.getenv("TEMP_CHANGE_THRESHOLD", "0.5"))

# How often to send data even if temperature hasn't changed (seconds)
HEARTBEAT_INTERVAL = float(os.getenv("TEMP_HEARTBEAT_INTERVAL", "60.0"))


class TemperatureSensor:
    """Reads temperature from a DS18B20 sensor via the 1-Wire sysfs interface."""

    def __init__(self):
        self.device_path = None
        self.last_temperature = None
        self.last_report_time = 0

        self._discover_sensor()

    def _discover_sensor(self):
        """Auto-discover the DS18B20 sensor on the 1-Wire bus."""
        try:
            devices = glob.glob(os.path.join(W1_DEVICES_PATH, W1_DEVICE_PREFIX + "*"))
            if not devices:
                logging.error(
                    "No DS18B20 sensor found! "
                    "Make sure 1-Wire is enabled (dtoverlay=w1-gpio in /boot/config.txt) "
                    "and the sensor is properly wired with a 4.7kΩ pull-up resistor."
                )
                return

            # Use the first sensor found
            self.device_path = os.path.join(devices[0], "w1_slave")
            device_id = os.path.basename(devices[0])
            logging.info(f"DS18B20 sensor found: {device_id}")

            if len(devices) > 1:
                logging.info(f"Multiple sensors detected ({len(devices)}), using first: {device_id}")

        except Exception as e:
            logging.error(f"Error discovering DS18B20 sensor: {e}")

    def read_temperature(self):
        """
        Read temperature from the DS18B20 sensor.

        Returns:
            float: Temperature in °C, or None if reading failed.
        """
        if self.device_path is None:
            return None

        try:
            with open(self.device_path, 'r') as f:
                lines = f.readlines()

            # The w1_slave file has two lines:
            # Line 1: xx xx xx xx xx xx xx xx xx : crc=xx YES/NO
            # Line 2: xx xx xx xx xx xx xx xx xx t=XXXXX
            if len(lines) < 2:
                logging.warning("Unexpected sensor output format")
                return None

            # Check CRC validity
            if "YES" not in lines[0]:
                logging.warning("CRC check failed, retrying...")
                return None

            # Parse temperature from second line
            temp_pos = lines[1].find("t=")
            if temp_pos == -1:
                logging.warning("Temperature value not found in sensor output")
                return None

            temp_string = lines[1][temp_pos + 2:]
            temp_celsius = float(temp_string) / 1000.0

            # Sanity check — DS18B20 range is -55°C to +125°C
            if temp_celsius < -55 or temp_celsius > 125:
                logging.warning(f"Temperature out of range: {temp_celsius}°C")
                return None

            return round(temp_celsius, 1)

        except FileNotFoundError:
            logging.error(f"Sensor file not found: {self.device_path}")
            self.device_path = None
            return None
        except Exception as e:
            logging.error(f"Error reading temperature: {e}")
            return None

    def start(self, callback=None):
        """
        Main loop: continuously read temperature and report significant changes.

        Args:
            callback: Optional function(temp_data_dict) called on temperature changes.
        """
        if self.device_path is None:
            logging.error("Cannot start: No DS18B20 sensor found.")
            logging.error("Check wiring and ensure 1-Wire is enabled in /boot/config.txt.")
            return

        logging.info("Temperature reader started.")
        logging.info(f"  Read interval: {READ_INTERVAL}s")
        logging.info(f"  Change threshold: {CHANGE_THRESHOLD}°C")
        logging.info(f"  Heartbeat interval: {HEARTBEAT_INTERVAL}s")

        try:
            while True:
                temp = self.read_temperature()
                now = time.time()

                if temp is None:
                    time.sleep(READ_INTERVAL)
                    continue

                temp_changed = (
                    self.last_temperature is None
                    or abs(temp - self.last_temperature) >= CHANGE_THRESHOLD
                )
                heartbeat_due = (now - self.last_report_time) >= HEARTBEAT_INTERVAL

                if temp_changed or heartbeat_due:
                    reason = "change" if temp_changed else "heartbeat"
                    logging.info(f"Temperature: {temp}°C ({reason})")

                    self.last_temperature = temp
                    self.last_report_time = now

                    if callback:
                        data = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "temperature": temp,
                            "unit": "C",
                            "reason": reason,
                        }
                        callback(data)

                time.sleep(READ_INTERVAL)

        except KeyboardInterrupt:
            logging.info("Temperature reader stopped.")


def main():
    """Entry point when run as a module."""
    from src.db_connector import DatabaseConnector

    db = DatabaseConnector()
    sensor = TemperatureSensor()

    def on_temperature(data):
        """Callback when temperature changes or heartbeat fires."""
        logging.info(f"Sending temperature data: {data['temperature']}°C")
        db.send_temperature_data(data)

    sensor.start(callback=on_temperature)


if __name__ == "__main__":
    main()
