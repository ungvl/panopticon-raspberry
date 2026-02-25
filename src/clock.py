import time
from RPLCD.i2c import CharLCD
from datetime import datetime

# Initialize the LCD
# Address is usually 0x27. If it fails, run `i2cdetect -y 1` to confirm.
try:
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
                  cols=20, rows=4, dotsize=8)
except Exception as e:
    print(f"Error connecting to LCD: {e}")
    exit()

def run_clock():
    print("LCD Clock started. Press Ctrl+C to stop.")
    lcd.clear()
    
    # We use a simple counter to only clear the screen if needed, 
    # preventing that annoying "flicker" on every update.
    last_minute = -1

    try:
        while True:
            now = datetime.now()
            
            # Formatting strings
            date_str = now.strftime("%A, %b %d")
            time_str = now.strftime("%I:%M:%S %p")
            
            # Row 1: Date (Centered)
            lcd.cursor_pos = (1, 0)
            lcd.write_string(date_str.center(20))
            
            # Row 2: Time (Centered)
            lcd.cursor_pos = (2, 0)
            lcd.write_string(time_str.center(20))
            
            # Row 3: Optional Status (e.g., Appwrite Link)
            lcd.cursor_pos = (3, 0)
            lcd.write_string("System Active".center(20))

            time.sleep(1)
            
    except KeyboardInterrupt:
        lcd.clear()
        lcd.backlight_enabled = False
        print("\nClock stopped and backlight off.")

if __name__ == "__main__":
    run_clock()