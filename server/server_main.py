from server_chat import chat_main
from server_stream import stream_main
import threading

def run_chat_server():
    chat_main()

def run_stream_server():
    stream_main()

if __name__ == "__main__":
    chat_thread = threading.Thread(target=run_chat_server)
    stream_thread = threading.Thread(target=run_stream_server)

    chat_thread.start()
    stream_thread.start()

    chat_thread.join()
    stream_thread.join()