# Streaming Platform App

This application replicates a streaming platform like Twitch. It provides a chat server, a video streaming server, and a screen sharing server. The chat server allows multiple clients to join a chatroom, exchange messages, and perform administrative tasks like kicking users and promoting users to admins. The video streaming server captures frames from a webcam and streams them to connected clients, while the screen sharing server captures the screen and streams it to connected clients.

## Features

### Chat Server
- **Broadcast messages**: Broadcasts messages to all connected clients.
- **Private messages**: Send private messages to specific users - `/private <nickname> message`
- **Admin commands**:
  - `/kick <nickname>`: Kick a user from the chat (admin only).
  - `/addadmin <nickname>`: Promote a user to admin (admin only).
  - `/listusers`: List all connected users.
  - `/listadmins`: List all admin users (admin only).

### Video Streaming Server
- **Webcam streaming**: Captures frames from the webcam and streams them to connected clients.
- **Frame rate control**: Configurable frame rate for streaming.

### Screen Sharing Server
- **Screen capture**: Captures the screen and streams it to connected clients.
- **Frame rate control**: Configurable frame rate for streaming.

## Requirements

- Python 3.11.5
- `opencv-python`
- `pyautogui`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/mainakm7/streaming_platform_app.git
    ```

2. Install the required packages:
    ```sh
    pip install opencv-python pyautogui pillow
    ```

## Usage

1. **Run the chat server:**
    ```sh
    python server_chat.py
    ```
    This will start the chat server.

2. **Run the video distribution server:**
    ```sh
    python stream_video_distribution.py
    ```
    This will start the video distribution server.

3. **Run the screen share distribution server:**
    ```sh
    python stream_screenshare_distribution.py
    ```
    This will start the screen share distribution server.

4. **Run the video host:**
    ```sh
    python stream_video_host.py
    ```
    This will start the video host and stream webcam data to the video distribution server.

5. **Run the screen share host:**
    ```sh
    python stream_screenshare_host.py
    ```
    This will start the screen share host and stream screen data to the screen share distribution server.

6. **Connect to the chat server:**
    Make sure to update the server HOST IP properly.
    - After connecting, enter a nickname when prompted.

7. **Connect to the video streaming server and screen sharing server:**
    Use a client script to connect to the video streaming server and the screen sharing server to display the streamed video and screen.

## Files

### Server
- `server_chat.py`: Contains the chat server implementation.
- `stream_video_distribution.py`: Contains the video distribution server implementation.
- `stream_screenshare_distribution.py`: Contains the screen share distribution server implementation.

### Host
- `stream_video_host.py`: Main script to run the video host.
- `stream_screenshare_host.py`: Main script to run the screen share host.

### Client
- `client_gui.py`: Main script to run the client-side script.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements. Please ensure any changes are well-documented and tested.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Python's `socket` module for providing the core functionality.
- `opencv-python` for video capture and processing.
- `pyautogui` for screen capture.
- `tkinter` for the graphical user interface.
- Inspiration from various network programming resources.
