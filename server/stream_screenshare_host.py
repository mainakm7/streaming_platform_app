import socket
import threading
import pyautogui
import base64
from io import BytesIO
import time

DISTRIBUTION_HOST = "localhost"
DISTRIBUTION_PORT = 12348

HOST = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST.connect((DISTRIBUTION_HOST, DISTRIBUTION_PORT))

def send_screen(host):
    while True:
        try:
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.resize((800, 600))
            
            buffer = BytesIO()
            screenshot.save(buffer, format="JPEG")
            screenshot_bytes = buffer.getvalue()

            frame_encode = base64.b64encode(screenshot_bytes).decode("utf-8")
            host.sendall((frame_encode + "<END>").encode("utf-8"))
            time.sleep(0.1)  # Add a small delay to control the frame rate
        except Exception as e:
            print(f"Error sending screen info: {e}")
            host.close()
            break

def screen_main():
    screen_thread = threading.Thread(target=send_screen, args=(HOST,))
    screen_thread.start()

if __name__ == "__main__":
    screen_main()
