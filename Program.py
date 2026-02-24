from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import ImageDraw, ImageFont, Image
from time import sleep
from datetime import datetime

# Initialize the I2C interface and the SSD1306 OLED display
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

# Load a font (you can replace this with a TTF font if desired)
font = ImageFont.load_default()

def display_time():
    while True:
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
            
            # Display the image
            device.display(image)
        
        # Update every second
        sleep(1)

if __name__ == "__main__":
    try:
        display_time()
    except KeyboardInterrupt:
        pass