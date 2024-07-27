from server_chat import chat_main
from server_stream import stream_main
import threading
import signal

stop_event = threading.Event()

def run_chat_server():
    chat_main(stop_event)

def run_stream_server():
    stream_main(stop_event)

def signal_handler(sig, frame):
    print("Signal received, shutting down...")
    stop_event.set()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    chat_thread = threading.Thread(target=run_chat_server)
    stream_thread = threading.Thread(target=run_stream_server)

    chat_thread.start()
    stream_thread.start()

    chat_thread.join()
    stream_thread.join()

    print("Servers shut down gracefully.")
