import socket
import base64
import cv2
import numpy as np
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext

CHAT_SERVER_HOST = "localhost"
CHAT_SERVER_PORT = 12345
STREAM_SERVER_HOST = "localhost"
STREAM_SERVER_PORT = 12346
BUFFER_SIZE = 2**16
MAX_CHUNK_SIZE = 4096

class Client:
    def __init__(self, chathost, chatport, streamhost, streamport, buffersize):
        self.streamhost = streamhost
        self.streamport = streamport
        self.chathost = chathost
        self.chatport = chatport
        self.buffersize = buffersize

        self.chat_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chat_client.connect((self.chathost, self.chatport))

        self.stream_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stream_client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffersize)

        self._nickname = self.nickname()
        
        self.running = True
        self.gui_done = False
        self.chatbox = None

        self.stop_event = threading.Event()

        self.chat_receive_thread = threading.Thread(target=self.chat_receive_msg)
        self.chat_receive_thread.start()

        self.stream_receive_thread = threading.Thread(target=self.stream_receive)
        self.stream_receive_thread.start()

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

        self.chatlabel = tk.Label(self.chatframe, text="All chat", font=("Arial", 12))
        self.chatlabel.grid(row=0, column=0, padx=5, pady=5)

        self.chat_area = scrolledtext.ScrolledText(self.chatframe)
        self.chat_area.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.chat_area.config(state="disabled")

        self.pvtchatlabel = tk.Label(self.chatframe, text="Private chat", font=("Arial", 12))
        self.pvtchatlabel.grid(row=0, column=1, padx=5, pady=5)

        self.pvtchat_area = scrolledtext.ScrolledText(self.chatframe)
        self.pvtchat_area.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.pvtchat_area.config(state="disabled")

        self.msgframe = tk.Frame(self.chatbox)
        self.msgframe.pack(fill="x", padx=5, pady=5)

        self.msglabel = tk.Label(self.msgframe, text="Your messages here:", font=("Arial", 12))
        self.msglabel.pack(anchor="w")

        self.msg_area = tk.Text(self.msgframe, height=4)
        self.msg_area.pack(fill="x", padx=5, pady=5)

        self.button = tk.Button(self.chatbox, text="Send All Msg", font=("Arial", 10), command=self.write_msg)
        self.button.pack(padx=5, pady=5)

        self.gui_done = True
        self.chatbox.protocol("WM_DELETE_WINDOW", self.stop)
        self.chatbox.mainloop()

    def stream_receive(self):
        while self.running and not self.stop_event.is_set():
            try:
                self.stream_client.sendto(b'I want to join stream!', (self.streamhost, self.streamport))
                frame_data = b""
                while True:
                    chunk, _ = self.stream_client.recvfrom(MAX_CHUNK_SIZE)
                    if chunk == b'END':
                        break
                    frame_data += chunk
                
                data_decode2 = base64.b64decode(frame_data.decode('utf-8'))
                frame = np.frombuffer(data_decode2, dtype=np.uint8)
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow("Stream Video", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            except Exception as e:
                print(f"Error occurred while receiving stream: {e}")
                break
        cv2.destroyAllWindows()

    def chat_receive_msg(self):
        while self.running and not self.stop_event.is_set():
            try:
                msg = self.chat_client.recv(1024).decode("utf-8")
                if msg == "NICKNAME":
                    self.chat_client.send(self._nickname.encode("utf-8"))
                elif msg == "NICKNAME in use, please change":
                    self._nickname = self.new_nickname()
                    self.chat_client.send(self._nickname.encode("utf-8"))
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
        msg = f"{self._nickname}: {self.msg_area.get('1.0', 'end')}"
        self.chat_client.send(msg.encode("utf-8"))
        self.msg_area.delete("1.0", "end")

    def stop(self):
        self.running = False
        self.stop_event.set()
        self.chat_client.close()
        self.stream_client.close()
        self.chatbox.destroy()

    def restart_gui(self):
        self.chatbox.destroy()
        self.gui()

if __name__ == "__main__":
    client = Client(CHAT_SERVER_HOST, CHAT_SERVER_PORT, STREAM_SERVER_HOST, STREAM_SERVER_PORT, BUFFER_SIZE)
