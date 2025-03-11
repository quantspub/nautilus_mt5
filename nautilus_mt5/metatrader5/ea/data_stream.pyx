import threading
import json
import pytz
import socket
import select
import asyncio
import websockets
from datetime import datetime


cdef class MetaTrader5Streamer:
    """
    This class manages data streaming using threading and socket-based options, 
    functioning as a callback server. With WebSocket support, the server can remain operational continuously, 
    allowing clients to connect and disconnect as needed without requiring a server restart for new subscriptions.  
    
    Parameters:
        host (str): Host address for the socket connection. Default is "127.0.0.1".
        callback_port (int): Port number for the streaming socket. Default is 15557.
        ws_port (int): Port number for websockets live data streaming. Default is 15558.
        callback (callable): Callback function to handle the streamed data. Default is None.
        stream_interval (float): Interval in seconds for data streaming. Default is 0.025.
        use_socket (bool): Whether to use sockets for streaming. Default is True.
        use_websockets (bool): Whether to use WebSockets for streaming. Default is True.
        debug (bool): Whether to enable debug messages. Default is False.
    """
    def __init__(self,
                 str host="127.0.0.1",
                 int callback_port=15557,
                 int ws_port=15558,
                 callback=None,
                 float stream_interval=0.025,
                 bint use_socket=True,
                 bint use_websockets=True,
                 bint debug=False):
        self.host = host
        self.callback_port = callback_port
        self.ws_port = ws_port
        self.callback = callback
        self.stream_interval = stream_interval
        self.use_socket = use_socket
        self.use_websockets = use_websockets
        
        self.debug = debug

        self.buffer_size = 16384
        self.stream_tasks = {}
        self.stream_thread = None
        self.stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stream_stop_event = threading.Event()

        # websockets
        self.ws_server = None
        self.connected_clients = set()

    cdef void _run_streaming_loop(self):
        """
        Runs the event loop for managing streaming tasks in a separate thread.
        """
        try:
            self.stream_stop_event.clear()
            if self.use_socket:
                self._stream_socket()
            else:
                while not self.stream_stop_event.is_set():
                    for task_id, task_info in self.stream_tasks.items():
                        symbol, interval, callback, kwargs = task_info
                        try:
                            self._stream_data(symbol, interval, callback, kwargs)
                        except Exception as e:
                            if self.debug:
                                print(f"Error in streaming loop for task {task_id}: {e}")
                    self.stream_stop_event.wait(0.01)  # Prevent tight looping
        except Exception as e:
            if self.debug:
                print(f"Critical error in _run_streaming_loop: {e}")

    cdef void _add_time_human(self, obj):
        """
        Adds a human-readable timestamp to the data object.

        Parameters:
            obj (dict or list): Data object to modify.
        """
        required_tz = pytz.timezone("Etc/UTC")
        if isinstance(obj, dict):
            if "time" in obj:
                time_obj = datetime.fromtimestamp(obj["time"], required_tz)
                obj["time_human"] = time_obj.strftime("%Y-%m-%d %H:%M:%S")
            for value in obj.values():
                self._add_time_human(value)
        elif isinstance(obj, list):
            for item in obj:
                self._add_time_human(item)

    cdef void _stream_socket(self):
        """
        Sets up the socket for streaming and processes incoming data.
        """
        if self.debug:
            print(f"Initializing socket on {self.host}:{self.callback_port}")
        self.stream_socket.bind((self.host, self.callback_port))
        self.stream_socket.listen(10)
        self.stream_socket.setblocking(False)

        if self.debug:
            print("Socket initialized and listening for connections.")
        while not self.stream_stop_event.is_set():
            try:
                ready_to_read, _, _ = select.select([self.stream_socket], [], [], 0.1)
                if ready_to_read:
                    conn, addr = self.stream_socket.accept()
                    if self.debug:
                        print(f"Connection accepted from {addr}")
                    data = conn.recv(self.buffer_size)
                    if not data:
                        conn.close()
                        continue

                    try:
                        json_data = json.loads(data.decode("utf-8").replace("\x00", ""))
                    except json.JSONDecodeError as e:
                        if self.debug:
                            print(f"JSON decode error: {e}")
                        conn.close()
                        continue

                    self._add_time_human(json_data)
                    formatted_data = json.dumps(json_data, indent=4)

                    if self.callback:
                        self.callback(formatted_data)
                    if self.debug:
                        print(f"Streaming data: {formatted_data}")
            except socket.error as e:
                if e.errno != 10035:  # Ignore non-blocking operation could not be completed immediately
                    if self.debug:
                        print(f"Error in _stream_socket: {e}")

                    raise socket.error("Socket error occurred while attempting to connect to the server.")
            except Exception as e:
                if self.debug:
                    print(f"Error in _stream_socket: {e}")
                raise RuntimeError("Error occurred while streaming data.")

    cdef void _start_ws_server(self):
        """
        Starts the WebSocket server for streaming data.

        This method initializes and starts the WebSocket server, allowing clients to connect and receive streamed data.
        """
        if self.debug:
            print(f"WebSocket server listening on {self.host}:{self.ws_port}")

        self.ws_server = websockets.serve(self.ws_handler, self.host, self.ws_port)
        asyncio.get_event_loop().run_until_complete(self.ws_server)
        asyncio.get_event_loop().run_forever()

    cdef void _stream_data(self, str symbol, float interval, callback, dict kwargs):
        """
        Streams data for a specific symbol, invoking the callback.

        Parameters:
            symbol (str): The trading symbol.
            interval (float): Streaming interval in seconds.
            callback (callable): Function to fetch data for the symbol.
            kwargs (dict): Additional arguments for the callback.
        """
        try:
            while not self.stream_stop_event.is_set():
                try:
                    data = callback(symbol, **kwargs)
                    if self.callback:
                        self.callback(data)
                    self.stream_stop_event.wait(interval)
                except Exception as e:
                    if self.debug:
                        print(f"Error while streaming data for {symbol}: {e}")
                    break
        except Exception as e:
            if self.debug:
                print(f"Critical error in _stream_data for {symbol}: {e}")

    async def ws_handler(self, websocket, path):
        """
        Handles incoming WebSocket connections.

        Parameters:
            websocket (WebSocketServerProtocol): The WebSocket connection instance.
            path (str): The URL path of the WebSocket connection.
        """
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                if self.debug:
                    print(f"Received message: {message}")
                # Process the message if needed
        finally:
            self.connected_clients.remove(websocket)

    cpdef void create_streaming_task(self, str req_id, list symbols, float interval, callback, dict kwargs):
        """
        Adds streaming tasks for the specified symbols.
        """
        for symbol in symbols:
            task_id = f"{symbol}-{req_id}"
            if task_id not in self.stream_tasks:
                self.stream_tasks[task_id] = (symbol, interval, callback, kwargs)
                if self.debug:
                    print(f"Task {task_id} added to stream_tasks.")

    cpdef void stop_streaming_task(self, str req_id, list symbols):
        """
        Removes streaming tasks for the specified symbols.
        """
        for symbol in symbols:
            task_id = f"{symbol}-{req_id}"
            if task_id in self.stream_tasks:
                del self.stream_tasks[task_id]
                if self.debug:
                    print(f"Task {task_id} removed from stream_tasks.")

    cpdef void start(self):
        """
        Starts the streaming loop in a separate thread.
        """
        if self.debug:
            print("Starting the streaming process.")
        self.stream_thread = threading.Thread(target=self._run_streaming_loop, daemon=True)
        self.stream_thread.start()

        if self.use_websockets:
                self._start_ws_server()

    cpdef void stop(self):
        """
        Stops the streaming process and cleans up resources.
        """
        if self.debug:
            print("Stopping the streaming process.")
        self.stream_stop_event.set()
        if self.use_socket:
            self.stream_socket.close()
        if self.stream_thread:
            self.stream_thread.join()

        if self.use_websockets and self.ws_server:
            self.ws_server.ws_server.close()
            # asyncio.get_event_loop().stop()
            self.ws_server = None
            if self.debug:
                print("WebSocket server stopped.")

    cpdef bint is_running(self):
        """
        Checks whether the streaming loop is currently active.
        """
        return self.stream_thread is not None and self.stream_thread.is_alive()

    cpdef void set_callback(self, callback):
        """
        Updates the callback function for handling streamed data.
        """
        if self.debug:
            print("Setting the callback function.")
        self.callback = callback
