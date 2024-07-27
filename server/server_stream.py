import threading
import socket
import cv2
import base64
import time

STREAM_HOST = "localhost"
STREAM_PORT = 12346
BUFFER_SIZE = 2**16
FRAME_RATE = 30  # Desired frame rate (frames per second)

def stream_main(stop_event):
    stream_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    stream_server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
    stream_server.bind((STREAM_HOST, STREAM_PORT))

    cap = cv2.VideoCapture(0)

    def stream():
        """Capture a frame from the webcam and encode it to base64."""
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            return None
        _, frame_data = cv2.imencode('.jpg', frame)
        frame_data_b64 = base64.b64encode(frame_data).decode('utf-8')
        return frame_data_b64

    def client_handler(address, frame):
        """Send the frame to the client."""
        try:
            stream_server.sendto(frame.encode('utf-8'), address)
        except Exception as e:
            print(f"Error sending message to client: {e}")

    print(f"Stream server is streaming on {STREAM_HOST}:{STREAM_PORT}")
    frame_interval = 1.0 / FRAME_RATE  # time interval between frames
    try:
        while not stop_event.is_set():
            try:
                stream_server.settimeout(1.0)  # timeout to allow checking the stop_event
                try:
                    _, client_address = stream_server.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    continue

                frame_data = stream()
                if frame_data is not None:
                    client_thread = threading.Thread(target=client_handler, args=(client_address, frame_data))
                    client_thread.start()
                else:
                    print("Failed to capture frame.")

                time.sleep(frame_interval)  # Sleep to control the frame rate

            except Exception as e:
                print(f"Error receiving data from client: {e}")

    except KeyboardInterrupt:
        print("Server is shutting down.")
    finally:
        cap.release()
        stream_server.close()
