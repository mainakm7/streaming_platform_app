import threading
import socket
import cv2
import base64
import time 

STREAM_HOST = "192.168.1.156"
STREAM_PORT = 12346
BUFFER_SIZE = 2**16
FRAME_RATE = 30  # Desired frame rate (frames per second)

STREAM_SERVER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
STREAM_SERVER.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
STREAM_SERVER.bind((STREAM_HOST, STREAM_PORT))

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
        STREAM_SERVER.sendto(frame.encode('utf-8'), address)  
    except Exception as e:
        print(f"Error sending message to client: {e}")

def stream_main():
    """Main function to run the server."""
    frame_interval = 1.0 / FRAME_RATE  # time interval between frames
    try:
        while True:
            try:
                _, client_address = STREAM_SERVER.recvfrom(BUFFER_SIZE)
                
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
        STREAM_SERVER.close()
