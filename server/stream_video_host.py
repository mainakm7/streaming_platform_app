import socket
import cv2
import base64
import time

VIDEO_DIST_HOST = "localhost"
VIDEO_DIST_PORT = 12346
BUFFER_SIZE = 2**16
FRAME_RATE = 30  # Desired frame rate (frames per second)
MAX_CHUNK_SIZE = 4096  # Maximum chunk size for UDP packets


def stream(cap):
    """Capture a frame from the webcam and encode it to base64."""
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame.")
        return None, None
    _, frame_data = cv2.imencode('.jpg', frame)
    frame_data_b64 = base64.b64encode(frame_data).decode('utf-8')
    return frame_data_b64, frame

def send_frame(video_host, frame_data):
    """Send the frame data to the client in chunks."""
    try:
        for i in range(0, len(frame_data), MAX_CHUNK_SIZE):
            chunk = frame_data[i:i + MAX_CHUNK_SIZE]
            video_host.sendall(chunk.encode('utf-8'))
        video_host.send(b'<END>')  # Indicate the end of the frame
    except Exception as e:
        print(f"Error sending frame data to distribution server: {e}")

def stream_main():
    
    video_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_host.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
    video_host.connect((VIDEO_DIST_HOST, VIDEO_DIST_PORT))

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Unable to open webcam.")
        exit(0)
    
    print(f"Streaming to distribution server at {VIDEO_DIST_HOST}:{VIDEO_DIST_PORT}")
    frame_interval = 1.0 / FRAME_RATE  # Time interval between frames

    try:
        while True:
            frame_data, frame = stream(cap)
            if frame_data:
                send_frame(video_host, frame_data)
            time.sleep(frame_interval)  # Sleep to control the frame rate
    except KeyboardInterrupt:
        print("Streaming stopped.")
    finally:
        cap.release()
        video_host.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    stream_main()
