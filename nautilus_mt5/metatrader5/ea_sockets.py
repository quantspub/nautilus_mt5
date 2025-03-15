import socket
import threading
import asyncio
from typing import Optional, Callable, Dict, List, Union


class EASocketConnection:
    """
    Manages the connection to a server for both REST and streaming communication.

    Attributes:
        host (str): The server host address.
        rest_port (int): The port for REST communication.
        stream_port (int): The port for streaming communication.
        stream_socket (Optional[socket.socket]): The socket for streaming communication.
        running (bool): Indicates if the streaming connection is active.
        encoding (str): The encoding used for message communication.
        stream_callback (Optional[Callable[[str], None]]): The callback function for streaming data.
        debug (bool): Enables debug mode for logging messages.
    """
    host: str
    rest_port: int
    stream_port: int
    stream_socket: Optional[socket.socket]
    running: bool
    encoding: str
    stream_callback: Optional[Callable[[str], None]]
    debug: bool

    def __init__(self, host: str = '127.0.0.1', rest_port: int = 15556, stream_port: int = 15557, encoding: str = 'utf-8', debug: bool = False) -> None:
        self.host = host
        self.rest_port = rest_port
        self.stream_port = stream_port
        self.stream_socket = None
        self.running = False
        self.encoding = encoding
        self.stream_callback = None
        self.debug = debug
        
    async def send_message(self, message: str) -> str:
        """
        Sends a request command/message to the server and returns the decoded response.

        :param message: The message to send.
        :return: The server's response as a decoded string.
        """
        try:
            reader, writer = await asyncio.open_connection(self.host, self.rest_port)
            writer.write(message.encode(self.encoding))
            await writer.drain()
            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            if self.debug:
                print(f"Sent: {message}, Received: {response.decode(self.encoding)}")
            return response.decode(self.encoding)
        except Exception as e:
            if self.debug:
                print(f"Error: {e}")
            return f"Error: {e}"

    def start_stream(self, callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Connects to the streaming server and continuously listens for updates.

        :param callback: Optional callback function to handle incoming stream data.
        """
        self.stream_callback = callback
        try:
            self.stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.stream_socket.connect((self.host, self.stream_port))
            self.running = True
            threading.Thread(target=self._listen_stream, daemon=True).start()
        except Exception as e:
            print(f"Streaming connection error: {e}")

    def _listen_stream(self) -> None:
        """ Internal method to listen for streaming data. """
        try:
            while self.running:
                data = self.stream_socket.recv(1024)
                if data:
                    decoded_data = data.decode(self.encoding)
                    if self.debug:
                        print(f"Stream Update: {decoded_data}")
                    if self.stream_callback:
                        self.stream_callback(decoded_data)
        except Exception as e:
            print(f"Streaming error: {e}")

    def stop_stream(self) -> None:
        """ Stops the streaming connection. """
        self.running = False
        if self.stream_socket:
            self.stream_socket.close()

def make_message(command: str, sub_command: str, parameters: List[str]) -> str:
    """
    Constructs a message in the format FXXX^Y^<parameters>.

    :param command: The command identifier (e.g., "F123").
    :param sub_command: The sub-command or parameter (e.g., "Y").
    :param parameters: A list of additional parameters (e.g., ["param1", "param2"]).
    :return: A formatted message string.
    """
    try:
        params_str = '^'.join(parameters)
        message = f"{command}^{sub_command}^{params_str}"
        return message
    except Exception as e:
        return f"Error: {str(e)}"


def parse_response_message(message: str) -> Union[Dict[str, Union[str, List[str]]], Dict[str, str]]:
    """
    Parses response message in the format FXXX^Y^<parameters>.
    The <parameters> part contains the server's response data.
    Handles hidden '^' delimiters and ensures data is properly extracted.

    :param message: The response or message string to parse.
    :return: A dictionary containing the command, sub_command, and data.
    """
    try:
        parts = message.split('^')
        if len(parts) < 3:
            raise ValueError("Invalid format. Expected at least three parts separated by '^'.")

        command, sub_command, *data = parts
        data = [d for d in data if d]

        if '' in data:
            raise ValueError("Invalid format. Hidden '^' delimiters detected in data.")

        return {'command': command, 'sub_command': sub_command, 'data': data}
    except Exception as e:
        return {'error': str(e)}
