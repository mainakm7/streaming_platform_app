import socket
import base64
import cv2
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import time
from io import BytesIO
from PIL import ImageGrab, Image
import pyautogui
import numpy as np

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
        self.chatbox = None
        
        self.stop_event = threading.Event()
        
        # Start the receiving messages thread
        self.chat_receive_thread = threading.Thread(target=self.chat_receive_msg)
        self.chat_receive_thread.start()
        
        self.video_stream_thread = threading.Thread(target=self.stream_video)
        self.video_stream_thread.start()
        
        # self.screen_stream_thread = threading.Thread(target=self.stream_screen)
        # self.screen_stream_thread.start()
        
        # Start the GUI in the main thread
        self.gui()

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
        self.chatbox = tk.Tk()
        self.chatbox.geometry("800x600")
        self.chatbox.title(f"Welcome to the chatroom: {self._nickname}")
        
        self.chatframe = tk.Frame(self.chatbox)
        self.chatframe.pack(expand=True, fill="both", padx=5, pady=5)
        self.chatframe.columnconfigure(0, weight=1)
        self.chatframe.columnconfigure(1, weight=1)
        
        # All chat widget
        self.chatlabel = tk.Label(self.chatframe, text="All chat", font=("Arial", 12))
        self.chatlabel.grid(row=0, column=0, padx=5, pady=5)
        
        self.chat_area = scrolledtext.ScrolledText(self.chatframe)
        self.chat_area.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.chat_area.config(state="disabled")
        
        # Private chat widget
        self.pvtchatlabel = tk.Label(self.chatframe, text="Private chat", font=("Arial", 12))
        self.pvtchatlabel.grid(row=0, column=1, padx=5, pady=5)
        
        self.pvtchat_area = scrolledtext.ScrolledText(self.chatframe)
        self.pvtchat_area.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.pvtchat_area.config(state="disabled")
        
        # Message input frame
        self.msgframe = tk.Frame(self.chatbox)
        self.msgframe.pack(fill="x", padx=5, pady=5)
        
        self.msglabel = tk.Label(self.msgframe, text="Your messages here:", font=("Arial", 12))
        self.msglabel.pack(anchor="w")
        
        self.msg_area = tk.Text(self.msgframe, height=4)
        self.msg_area.pack(fill="x", padx=5, pady=5)
        
        # Send button
        self.button = tk.Button(self.chatbox, text="Send All Msg", font=("Arial", 10), command=self.write_msg)
        self.button.pack(padx=5, pady=5)
        
        self.gui_done = True
        self.chatbox.protocol("WM_DELETE_WINDOW", self.stop)
        self.chatbox.mainloop()
    
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
                    cv2.imshow("Stream:", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    
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

                # Check for user input to quit the streaming
                key = cv2.waitKey(1) & 0xFF
                if key == ord('w'):
                    self.running = False
                    break

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
        while self.running and not self.stop_event.is_set():
            try:
                msg = self.chat_server.recv(1024).decode("utf-8")
                if msg == "NICKNAME":
                    self.chat_server.send(self._nickname.encode("utf-8"))
                elif msg == "NICKNAME in use, please change":
                    self._nickname = self.new_nickname()
                    self.chat_server.send(self._nickname.encode("utf-8"))
                    if self.chatbox is not None:
                        self.chatbox.after(0, self.restart_gui)
                elif msg.startswith("Private from"):
                    if self.chatbox is not None:
                        self.chatbox.after(0, self.display_private_msg, msg)
                else:
                    if self.chatbox is not None:
                        self.chatbox.after(0, self.display_msg, msg)
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
    
    def stop(self):
        self.running = False
        self.stop_event.set()
        self.chat_server.close()
        self.video_server.close()
        self.screen_server.close()
        if self.chatbox:
            self.chatbox.destroy()
        cv2.destroyAllWindows()

    def restart_gui(self):
        self.chatbox.destroy()
        self.gui()
        
if __name__ == "__main__":
    host = StreamHost(CHAT_SERVER_HOST, CHAT_SERVER_PORT, VIDEO_SERVER_HOST, VIDEO_SERVER_PORT, 
                    SCREEN_SERVER_HOST, SCREEN_SERVER_PORT, BUFFER_SIZE, FRAME_RATE, MAX_CHUNK_SIZE)
