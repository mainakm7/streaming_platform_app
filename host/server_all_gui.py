import socket
import base64
import cv2
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import time
from io import BytesIO
from PIL import ImageTk, Image
import pyautogui
import numpy as np
import signal
import sys

CHAT_SERVER_HOST = "localhost"
CHAT_SERVER_PORT = 12345
VIDEO_SERVER_HOST = "localhost"
VIDEO_SERVER_PORT = 12346
SCREEN_SERVER_HOST = "localhost"
SCREEN_SERVER_PORT = 12347
BUFFER_SIZE = 2**16
FRAME_RATE = 30
MAX_CHUNK_SIZE = 4096

class StreamHost:
    def __init__(self, chathost, chatport, videohost, videoport, screenhost, screenport, buffersize, framerate, maxchunk):
        self.videohost = videohost
        self.videoport = videoport
        self.screenhost = screenhost
        self.screenport = screenport
        self.chathost = chathost
        self.chatport = chatport
        self.buffersize = buffersize
        self.framerate = framerate
        self.maxchunk = maxchunk
        
        self.chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chat_server.connect((self.chathost, self.chatport))
        
        self.video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffersize)
        self.video_server.connect((self.videohost, self.videoport))
        
        self.screen_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.screen_server.connect((self.screenhost, self.screenport))
        
        self._nickname = self.nickname()
        
        self.running = True
        self.gui_done = False
        
        # Start the receiving messages thread
        self.chat_receive_thread = threading.Thread(target=self.chat_receive_msg)
        self.chat_receive_thread.start()
        
        self.video_stream_thread = threading.Thread(target=self.stream_video)
        self.video_stream_thread.start()
        
        # Uncomment if screen streaming is needed
        # self.screen_stream_thread = threading.Thread(target=self.stream_screen)
        # self.screen_stream_thread.start()
        
        # Start the GUI in the main thread
        self.gui()

        # Register keyboard interrupt handler
        signal.signal(signal.SIGINT, self.keyboard_interrupt)

    def nickname(self):
        temp_root = tk.Tk()
        temp_root.withdraw()  
        nickname = simpledialog.askstring("Nickname", "Please enter your nickname", parent=temp_root)
        temp_root.destroy()  
        return nickname
    
    def new_nickname(self):
        temp_root = tk.Tk()
        temp_root.withdraw()  
        nickname = simpledialog.askstring("Nickname", "Please enter another nickname; Old one taken", parent=temp_root)
        temp_root.destroy()  
        return nickname

    def gui(self):
        self.streamframe = tk.Tk()
        self.streamframe.geometry("1200x600")
        self.streamframe.title(f"Welcome to the Stream: {self._nickname}")

        self.totframe = tk.Frame(self.streamframe)
        self.totframe.pack(expand=True, fill="both", padx=5, pady=5)
        self.totframe.columnconfigure(0, weight=1)
        self.totframe.columnconfigure(1, weight=2)
        self.totframe.columnconfigure(2, weight=2)

        # Video Stream Widget
        self.videoframelabel = tk.Label(self.totframe, text="Video stream", font=("Arial", 12))
        self.videoframelabel.grid(row=0, column=0, padx=5, pady=5)
        self.videoframe = tk.Label(self.totframe, text="Video stream will appear here") 
        self.videoframe.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # All Chat Widget
        self.chatlabel = tk.Label(self.totframe, text="All chat", font=("Arial", 12))
        self.chatlabel.grid(row=0, column=1, padx=5, pady=5)
        self.chat_area = scrolledtext.ScrolledText(self.totframe, state="disabled")
        self.chat_area.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Private Chat Widget
        self.pvtchatlabel = tk.Label(self.totframe, text="Private chat", font=("Arial", 12))
        self.pvtchatlabel.grid(row=0, column=2, padx=5, pady=5)
        self.pvtchat_area = scrolledtext.ScrolledText(self.totframe, state="disabled")
        self.pvtchat_area.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")

        # Message Input Frame
        self.msgframe = tk.Frame(self.streamframe)
        self.msgframe.pack(fill="x", padx=5, pady=5)

        self.msglabel = tk.Label(self.msgframe, text="Your messages here:", font=("Arial", 12))
        self.msglabel.pack(anchor="w")

        self.msg_area = tk.Text(self.msgframe, height=4)
        self.msg_area.pack(fill="x", padx=5, pady=5)

        # Send Button
        self.button = tk.Button(self.streamframe, text="Send All Msg", font=("Arial", 10), command=self.write_msg)
        self.button.pack(padx=5, pady=5)

        self.gui_done = True
        self.streamframe.protocol("WM_DELETE_WINDOW", self.stop)
        self.streamframe.mainloop()
    
    def stream_video(self):
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
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Unable to open webcam.")
            return
        
        print(f"Streaming to distribution server at {self.videohost}:{self.videoport}")
        frame_interval = 1.0 / self.framerate  # Time interval between frames

        try:
            while self.running:
                frame_data, frame = stream(cap)
                if frame_data:
                    send_frame(self.video_server, frame_data)
                if frame is not None:
                    # Convert OpenCV frame to PIL Image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    tk_image = ImageTk.PhotoImage(image=pil_image)
                    
                    # Update Tkinter Label with new image
                    self.videoframe.config(image=tk_image)
                    self.videoframe.image = tk_image  # Keep a reference to avoid garbage collection

                    # Handle GUI update
                    self.streamframe.update_idletasks()
                    self.streamframe.update()
                    
                time.sleep(frame_interval)
        except KeyboardInterrupt:
            print("Streaming stopped.")
        finally:
            cap.release()
            self.video_server.close()
            cv2.destroyAllWindows()

    def stream_screen(self):
        frame_interval = 1.0 / self.framerate
        print(f"Streaming to distribution server at {self.screenhost}:{self.screenport}")

        while self.running:
            try:
                # Take a screenshot and resize
                screenshot = pyautogui.screenshot()
                screenshot = screenshot.resize((800, 600))

                # Convert PIL image to OpenCV format
                open_cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # Display the image
                cv2.imshow("Screen Stream", open_cv_image)

                # Encode and send the screenshot
                buffer = BytesIO()
                screenshot.save(buffer, format="JPEG")
                screenshot_bytes = buffer.getvalue()
                frame_encode = base64.b64encode(screenshot_bytes).decode("utf-8")
                self.screen_server.sendall((frame_encode + "<END>").encode("utf-8"))

                # Delay to control frame rate
                time.sleep(frame_interval)
            except Exception as e:
                print(f"Error sending screen info: {e}")
                self.screen_server.close()
                self.running = False
                break

        # Clean up
        cv2.destroyAllWindows()

    def chat_receive_msg(self):
        while self.running:
            try:
                msg = self.chat_server.recv(1024).decode("utf-8")
                if msg == "NICKNAME":
                    self.chat_server.send(self._nickname.encode("utf-8"))
                elif msg == "NICKNAME in use, please change":
                    self._nickname = self.new_nickname()
                    self.chat_server.send(self._nickname.encode("utf-8"))
                    self.restart_gui()
                elif msg.startswith("Private from"):
                    self.display_private_msg(msg)
                else:
                    self.display_msg(msg)
            except Exception as e:
                print(f"Error occurred while receiving chat msg: {e}")
                break
    
    def display_msg(self, msg):
        if self.gui_done:
            self.chat_area.config(state="normal")
            self.chat_area.insert("end", msg + "\n")
            self.chat_area.yview("end")
            self.chat_area.config(state="disabled")
    
    def display_private_msg(self, msg):
        if self.gui_done:
            self.pvtchat_area.config(state="normal")
            self.pvtchat_area.insert("end", msg + "\n")
            self.pvtchat_area.yview("end")
            self.pvtchat_area.config(state="disabled")
    
    def write_msg(self):
        msg = f"{self.msg_area.get('1.0', 'end')}".strip()
        self.msg_area.delete("1.0", "end")
        self.chat_server.send(msg.encode("utf-8"))
    
    def restart_gui(self):
        self.streamframe.destroy()
        self.gui()

    def stop(self):
        self.running = False
        self.chat_server.close()
        self.video_server.close()
        self.screen_server.close()
        self.streamframe.destroy()
        print("Application stopped.")

    def keyboard_interrupt(self, signum, frame):
        """Handle keyboard interrupts (Ctrl+C) gracefully."""
        print("Keyboard interrupt received. Stopping...")
        self.stop()

if __name__ == "__main__":
    StreamHost(CHAT_SERVER_HOST, CHAT_SERVER_PORT, VIDEO_SERVER_HOST, VIDEO_SERVER_PORT, SCREEN_SERVER_HOST, SCREEN_SERVER_PORT, BUFFER_SIZE, FRAME_RATE, MAX_CHUNK_SIZE)
