# Streaming Platform App

This application replicates a streaming platform like Twitch. It provides a chat server and a video streaming server. The chat server allows multiple clients to join a chatroom, exchange messages, and perform administrative tasks like kicking users and promoting users to admins. The video streaming server captures frames from a webcam and streams them to connected clients.

## Features

### Chat Server
- **Broadcast messages**: Broadcasts messages to all connected clients.
- **Private messages**: Send private messages to specific users.
- **Admin commands**:
  - `/kick <nickname>`: Kick a user from the chat (admin only).
  - `/addadmin <nickname>`: Promote a user to admin (admin only).
  - `/listusers`: List all connected users.
  - `/listadmins`: List all admin users (admin only).

### Video Streaming Server
- **Webcam streaming**: Captures frames from the webcam and streams them to connected clients.
- **Frame rate control**: Configurable frame rate for streaming.

## Requirements

- Python 3.6 or later
- `opencv-python`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/mainakm7/streaming_platform_app.git
    ```

2. Install the required packages:
    ```sh
    pip install opencv-python
    ```

## Usage

1. **Run the server:**
    ```sh
    python server_main.py
    ```
    This will start both the chat server and the video streaming server.

2. **Connect to the chat server:**
    Use any Telnet client to connect to the chat server. For example:
    ```sh
    telnet 192.168.1.156 12345
    ```
    - After connecting, enter a nickname when prompted.

3. **Connect to the video streaming server:**
    Use a client script to connect to the video streaming server and display the streamed video.

## Files

### Server
- `server_main.py`: Main script to run both the chat and streaming servers.
- `server_chat.py`: Contains the chat server implementation.
- `server_stream.py`: Contains the video streaming server implementation.

### Client
- `client_gui.py`: Main script to run the client-side script.

## Stream

- The video stream sends video at 30 fps.

## Chat Features

The chatroom allows admins based on IP. Admins can use some special commands:

- Kick user based on username:
    ```
    /kick nickname
    ```
- List all admins:
    ```
    /listadmins
    ```
- Add a user as an admin:
    ```
    /addadmin nickname
    ```

All users can use the following commands:

- List all users:
    ```
    /listusers
    ```

- Send private messages to specific users:
    ```
    /private nickname msg
    ```

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements. Please ensure any changes are well-documented and tested.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Python's `socket` module for providing the core functionality. TCP is used for chat and UDP for video stream.
- `tkinter` for the graphical user interface.
- Inspiration from various network programming resources.
