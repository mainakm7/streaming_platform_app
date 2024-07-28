import socket
import pyautogui
import base64
from io import BytesIO
import time

DISTRIBUTION_HOST = "localhost"
DISTRIBUTION_PORT = 12348
FRAME_RATE = 10  # Frames per second

def send_screen(host):
    frame_interval = 1.0 / FRAME_RATE  # Time interval between frames

    while True:
        try:
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.resize((800, 600))
            
            buffer = BytesIO()
            screenshot.save(buffer, format="JPEG")
            screenshot_bytes = buffer.getvalue()

            frame_encode = base64.b64encode(screenshot_bytes).decode("utf-8")
            host.sendall((frame_encode + "<END>").encode("utf-8"))

            time.sleep(frame_interval)  # Add a delay to control the frame rate
        except Exception as e:
            print(f"Error sending screen info: {e}")
            host.close()
            break

def screen_main():
    try:
        host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host_socket.connect((DISTRIBUTION_HOST, DISTRIBUTION_PORT))
        print(f"Connected to distribution server at {DISTRIBUTION_HOST}:{DISTRIBUTION_PORT}")
        send_screen(host_socket)
    except Exception as e:
        print(f"Error connecting to distribution server: {e}")

if __name__ == "__main__":
    screen_main()
