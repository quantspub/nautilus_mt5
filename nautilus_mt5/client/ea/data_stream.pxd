from libc.stdint cimport int32_t, int64_t

cdef class MetaTrader5Streamer:
    """
    Manages streaming tasks for symbol data.

    Attributes:
        stream_tasks (dict): A dictionary to store streaming tasks.
        stream_thread (object): A thread to run the streaming loop.
        debug (bint): Flag to enable or disable debug messages.
        stream_socket (object): The socket for streaming data.
        stream_stop_event (object): Event to control the streaming loop.
        use_socket (bint): Flag to determine whether to use socket or normal loop.
        use_websockets (bint): Flag to determine whether to use WebSockets for streaming.
    """
    cdef str host
    cdef int callback_port, ws_port
    cdef float stream_interval
    cdef object callback
    cdef bint use_socket, use_websockets, debug
    cdef int buffer_size
    cdef dict stream_tasks
    cdef object stream_thread
    cdef object stream_socket
    cdef object stream_stop_event
    cdef object ws_server
    cdef set connected_clients

    cdef void _run_streaming_loop(self)
    cdef void _add_time_human(self, obj)
    cdef void _stream_socket(self)
    cdef void _start_ws_server(self)
    cdef void _stream_data(self, str symbol, float interval, callback, dict kwargs)
    cpdef void create_streaming_task(self, str req_id, list symbols, float interval, callback, dict kwargs)
    cpdef void stop_streaming_task(self, str req_id, list symbols)
    cpdef void start(self)
    cpdef void stop(self)
    cpdef bint is_running(self)
    cpdef void set_callback(self, callback)
