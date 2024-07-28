import threading
import socket
import cv2
import base64
import time
from concurrent.futures import ThreadPoolExecutor

STREAM_HOST = "localhost"
STREAM_PORT = 12346
BUFFER_SIZE = 2**16
FRAME_RATE = 30  # Desired frame rate (frames per second)
MAX_CHUNK_SIZE = 4096  # Maximum chunk size for UDP packets
MAX_THREADS = 10  # Maximum number of threads in the thread pool

stream_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
stream_server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
stream_server.bind((STREAM_HOST, STREAM_PORT))

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Unable to open webcam.")
    exit(0)

def stream():
    """Capture a frame from the webcam and encode it to base64."""
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame.")
        return None, None
    _, frame_data = cv2.imencode('.jpg', frame)
    frame_data_b64 = base64.b64encode(frame_data).decode('utf-8')
    return frame_data_b64, frame

def send_frame(address, frame_data):
    """Send the frame data to the client in chunks."""
    try:
        for i in range(0, len(frame_data), MAX_CHUNK_SIZE):
            chunk = frame_data[i:i + MAX_CHUNK_SIZE]
            stream_server.sendto(chunk.encode('utf-8'), address)
        stream_server.sendto(b'<END>', address)  # Indicate the end of the frame
    except Exception as e:
        print(f"Error sending message to client: {e}")
def stream_main():
    print(f"Stream server is streaming on {STREAM_HOST}:{STREAM_PORT}")
    frame_interval = 1.0 / FRAME_RATE  # Time interval between frames

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        try:
            while True:
                try:
                    _, client_address = stream_server.recvfrom(BUFFER_SIZE)

                    frame_data, frame_data_noencode = stream()
                    if frame_data:
                        executor.submit(send_frame, client_address, frame_data)

                    time.sleep(frame_interval)  # Sleep to control the frame rate

                except Exception as e:
                    print(f"Error receiving data from client: {e}")

        except KeyboardInterrupt:
            print("Server is shutting down.")
        finally:
            cap.release()
            stream_server.close()
            cv2.destroyAllWindows()

