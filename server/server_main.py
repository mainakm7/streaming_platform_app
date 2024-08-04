import threading
from server.server_chat import chat_main
from server.stream_video_distribution import dist_video_main
from server.stream_screen_distribution import dist_screen_main
if __name__ == "__main__":
    chat_thread = threading.Thread(target=chat_main)
    video_thread = threading.Thread(target=dist_video_main)
    screen_thread = threading.Thread(target=dist_screen_main)

    chat_thread.start()
    video_thread.start()
    screen_thread.start()

    chat_thread.join()
    video_thread.join()
    screen_thread.join()
