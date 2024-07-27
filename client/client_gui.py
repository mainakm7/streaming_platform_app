import threading
import socket
import tkinter as tk
from tkinter import scrolledtext, simpledialog
import cv2
import base64

SERVER_HOST = "localhost"  # Change to the server's public IP if needed
SERVER_CHAT_PORT = 12345
SERVER_STREAM_PORT = 12346

class Client:
    def __init__(self, host, port):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client.connect((host, port))
        
        self._nickname = self.nickname()
        
        self.running = True
        self.gui_done = False
        self.chatbox = None
        
        self.stop_event = threading.Event()
        
        # Start the receiving messages thread
        self.receive_thread = threading.Thread(target=self.receive_msg)
        self.receive_thread.start()
        
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
    
    def receive_msg(self):
        while self.running and not self.stop_event.is_set():
            try:
                msg = self._client.recv(1024).decode("utf-8")
                if msg == "NICKNAME":
                    self._client.send(self._nickname.encode("utf-8"))
                elif msg == "NICKNAME in use, please change":
                    self._nickname = self.new_nickname()
                    self._client.send(self._nickname.encode("utf-8"))
                    if self.chatbox is not None:
                        self.chatbox.after(0, self.restart_gui)
                elif msg.startswith("Private from"):
                    if self.chatbox is not None:
                        self.chatbox.after(0, self.display_private_msg, msg)
                else:
                    if self.chatbox is not None:
                        self.chatbox.after(0, self.display_msg, msg)
            except Exception as e:
                print(f"Error occurred while receiving msg: {e}")
                self.stop()
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
    
    def restart_gui(self):
        if self.chatbox:
            self.chatbox.quit()
            self.chatbox.destroy()
        self.gui()
    
    def write_msg(self):
        msg = self.msg_area.get("1.0", "end").strip()
        self.msg_area.delete("1.0", "end")
        try:
            self._client.send(msg.encode("utf-8"))
        except Exception as e:
            print(f"Error occurred while sending msg: {e}")
    
    def stop(self):
        self.running = False
        self.stop_event.set()
        if self.chatbox:
            self.chatbox.quit()
            self.chatbox.destroy()
        if self._client:
            try:
                self._client.shutdown(socket.SHUT_RDWR)
                self._client.close()
            except Exception as e:
                print(f"Error occurred while closing the socket: {e}")
        exit(0)

if __name__ == "__main__":
    NewClient = Client(SERVER_HOST, SERVER_PORT)
