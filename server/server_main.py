import threading
from server_chat import chat_main
from server_stream import stream_main

if __name__ == "__main__":
    chat_thread = threading.Thread(target=chat_main)
    stream_thread = threading.Thread(target=stream_main)

    chat_thread.start()
    stream_thread.start()

    chat_thread.join()
    stream_thread.join()
