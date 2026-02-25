from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import ImageDraw, ImageFont, Image
from time import sleep
from datetime import datetime
from gpiozero import Button
from statemachine import StateMachine, State
import asyncio
import ADS1x15

# Initialize the I2C interface and the SSD1306 OLED display
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

# Load a font (you can replace this with a TTF font if desired)
font = ImageFont.load_default()

def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read().strip()
            return f"CPU Temp: {int(temp)/1000:.1f} °C"
    except FileNotFoundError:
        return "CPU temperature file not found. Ensure the system is properly configured."
    except Exception as e:
        return f"An error occurred: {e}"

def get_fan_speed():
    # The typical path for the active cooler fan speed on Raspberry Pi 5
    # The 'hwmon2' part might change, so list the content of 'hwmon' if it doesn't work
    try:
        with open("/sys/devices/platform/cooling_fan/hwmon/hwmon1/fan1_input", "r") as f:
            speed = f.read().strip()
            return f"Fan Speed: {speed} RPM"
    except FileNotFoundError:
        return "Fan speed file not found. Ensure the fan is connected and detected, or check the correct path in /sys/devices/platform/cooling_fan/hwmon/"
    except Exception as e:
        return f"An error occurred: {e}"

async def display_time():
    while sm.current_state == sm.Info:
        # Create a blank image for drawing
        with Image.new("1", (device.width, device.height)) as image:
            draw = ImageDraw.Draw(image)
            
            # Get the current time
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # # Calculate text size and position
            # text_width, text_height = draw.textsize(current_time, font=font)
            # x = (device.width - text_width) // 2
            # y = (device.height - text_height) // 2

            x=5
            y=5
            
            # Draw the time on the display
            draw.text((x, y), current_time, font=font, fill=255)

            #Draw the fan speed on the display
            fan_speed = get_fan_speed()
            draw.text((x, y + 20), fan_speed, font=font, fill=255)

            #Draw the CPU temperature on the display
            cpu_temp = get_cpu_temperature()
            draw.text((x, y + 40), cpu_temp, font=font, fill=255)
            
            # Display the image
            device.display(image)
        
        # Update every second
        await asyncio.sleep(1)

async def display_joystick():
    while sm.current_state == sm.Joystick:
        # Create a blank image for drawing
        with Image.new("1", (device.width, device.height)) as image:
            draw = ImageDraw.Draw(image)
            
            # Display joystick information (placeholder)
            joystick_info = "Joystick Mode: Active"
            draw.text((5, 5), joystick_info, font=font, fill=255)
            
            x_value = ADS.read_adc(0, gain=1)  # Read from channel 0 (adjust as needed)
            y_value = ADS.read_adc(1, gain=1)  # Read from channel 1 (adjust as needed)

            print(f"Joystick X: {x_value}, Y: {y_value}")
            #draw.point((x_value // 256, y_value // 256), fill=255)  # Scale down for display

            # Display the image
            device.display(image)
        
        # Update every 100ms
        await asyncio.sleep(.1)

# Cecking button condition to switch modes
Joystick_button = Button(17, pull_up=False)  # GPIO pin 17 for the button

async def check_button():
    while True:
        if Joystick_button.is_pressed:
            sm.cycle()  # Switch between Info and Joystick states
            print("Button Pressed!")
            # Here you can add code to switch modes or perform any action when the button is pressed
        await asyncio.sleep(0.1)  # Check every 100ms
#Setting up state machine

ADS = ADS1x15.ADS1115(1,0x48)  # Create an instance of the ADS1115 ADC

async def status_reporter():
    while True:
        print(f"Current State: {sm.current_state}")
        await asyncio.sleep(3)  # Report status every 3 seconds


class ButtonCycle(StateMachine):
    "Control Info cycle"
    Info = State(initial=True)
    Joystick = State()

    cycle = (
        Info.to(Joystick)
        | Joystick.to(Info)
    )

    def before_cycle(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def on_enter_Joystick(self):
        print("Joystick has controll.")


    def on_exit_Joystick(self):
        print("Joystick has released control.")

sm = ButtonCycle()

async def main():
    print("Starting program...")
    print("starting button loop")
    task1 = asyncio.create_task(check_button())
    while True:
        if sm.current_state == sm.Info:
            display_time()
            await display_time()  # Run the time display loop
        elif sm.current_state == sm.Joystick:
            display_joystick()
            await display_joystick()  # Run the joystick display loop
        await asyncio.sleep(0.5)  # Main loop delay

if __name__ == "__main__":
    print("Program started.")
    asyncio.run(main())