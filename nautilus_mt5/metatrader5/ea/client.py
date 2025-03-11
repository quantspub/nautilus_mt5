from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from .connection import Connection
from .errors import ERROR_DICT

@dataclass 
class EAClientConfig:
    """
    Configuration for EAClient.

    Parameters:
        host (str): Host address for the EAClient. Default is "127.0.0.1".
        rest_port (int): Port number for REST API. Default is 15556.
        stream_port (int): Port number for streaming data. Default is 15557.
        encoding (str): Encoding type. Default is 'utf-8'.
        use_socket (bool): Whether to use sockets for communication. Default is True.
        enable_stream (bool): Flag to enable or disable streaming. Default is True.
        callback (Optional[Callable]): Callback function to handle streamed data. Default is None.
        debug (bool): Whether to enable debug messages. Default is False.
    """
    host: str = "127.0.0.1"
    rest_port: int = 15556
    stream_port: int = 15557
    encoding: str = 'utf-8'
    use_socket: bool = True
    enable_stream: bool = True
    callback: Optional[Callable] = None
    debug: bool = False
    
class EAClient(Connection):
    """
    Extends the Connection class to provide specific methods for interacting with the EA server.

    Attributes:
        return_error (str): Stores the error message for the last command.
        ok (bool): Indicates if the last command was successful.
    """
    def __init__(self, config: EAClientConfig) -> None:
        super().__init__(config.host, config.rest_port, config.stream_port, config.encoding, config.debug)
        self.config = config
        self.return_error = ''
        self.ok = False

    def _process_response(self, response: str, expected_code: str) -> Optional[Dict[str, Any]]:
        """
        Processes the server response and checks if it matches the expected code.

        :param response: The server response string.
        :param expected_code: The expected response code.
        :return: A dictionary of response parts if the response matches the expected code, otherwise None.
        """
        parsed_response = self.parse_response_message(response)
        if 'error' in parsed_response:
            if self.debug:
                print(parsed_response)

            self.timeout = True
            self.return_error = ERROR_DICT['99900']
            self.ok = False
            return None
        
        if parsed_response['command'] != expected_code:
            self.timeout = True
            self.return_error = ERROR_DICT['99900']
            self.ok = False
            return None

        self.timeout = False
        self.ok = True
        return parsed_response

    async def check_connection(self) -> bool:
        """
        Checks the connection to the server.

        :return: True if the connection is successful, otherwise False.
        """
        message = self.make_message('F000', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            return self._process_response(response, 'F000') is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Connection check failed: {error}")

    async def get_static_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves static account information from the server.

        :return: A dictionary containing static account information if successful, otherwise None.
        """
        message = self.make_message('F001', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F001')
            if parsed_response:
                return {
                    "name": parsed_response['data'][0],
                    "login": parsed_response['data'][1],
                    "currency": parsed_response['data'][2],
                    "type": parsed_response['data'][3],
                    "leverage": parsed_response['data'][4],
                    "trade_allowed": parsed_response['data'][5],
                    "limit_orders": parsed_response['data'][6],
                    "margin_call": parsed_response['data'][7],
                    "margin_close": parsed_response['data'][8],
                    "company": parsed_response['data'][9]
                }
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get static account info: {error}")

    async def get_dynamic_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves dynamic account information from the server.

        :return: A dictionary containing dynamic account information if successful, otherwise None.
        """
        message = self.make_message('F002', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F002')
            if parsed_response:
                return {
                    "balance": parsed_response['data'][0],
                    "equity": parsed_response['data'][1],
                    "profit": parsed_response['data'][2],
                    "margin": parsed_response['data'][3],
                    "margin_level": parsed_response['data'][4],
                    "margin_free": parsed_response['data'][5]
                }
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get dynamic account info: {error}")

    async def get_last_tick_info(self, instrument_name: str = 'EURUSD') -> Optional[Dict[str, Any]]:
        """
        Retrieves the last tick information for a given instrument.

        :param instrument_name: The name of the instrument.
        :return: A dictionary containing the last tick information if successful, otherwise None.
        """
        message = self.make_message('F020', '2', [instrument_name])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F020')
            if parsed_response:
                return {
                    "instrument": instrument_name,
                    "date": datetime.fromtimestamp(int(parsed_response['data'][0])).strftime('%Y-%m-%d %H:%M:%S'),
                    "bid": float(parsed_response['data'][1]),
                    "ask": float(parsed_response['data'][2]),
                    "last": float(parsed_response['data'][3]),
                    "volume": int(parsed_response['data'][4]),
                    "spread": float(parsed_response['data'][5]),
                    "date_in_ms": int(parsed_response['data'][6])
                }
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get last tick info: {error}")

    async def get_broker_server_time(self) -> Optional[Dict[str, int]]:
        """
        Retrieves the broker server time.

        :return: A dictionary containing the broker server time if successful, otherwise None.
        """
        message = self.make_message('F005', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F005')
            if parsed_response:
                timestamp = int(parsed_response['data'][0])
                dt = datetime.fromtimestamp(timestamp)
                my_date = {
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "second": dt.second
                }
                return my_date
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get broker server time: {error}")

    async def get_instrument_info(self, instrument_name: str = 'EURUSD') -> Optional[Dict[str, Any]]:
        """
        Retrieves information about a specific instrument.

        :param instrument_name: The name of the instrument.
        :return: A dictionary containing the instrument information if successful, otherwise None.
        """
        message = self.make_message('F003', '2', [instrument_name])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F003')
            if (parsed_response):
                return {
                    "instrument": instrument_name,
                    "digits": int(parsed_response['data'][0]),  # SYMBOL_DIGITS (Integer)
                    "max_lotsize": float(parsed_response['data'][1]),  # SYMBOL_VOLUME_MAX (Double)
                    "min_lotsize": float(parsed_response['data'][2]),  # SYMBOL_VOLUME_MIN (Double)
                    "lot_step": float(parsed_response['data'][3]),  # SYMBOL_VOLUME_STEP (Double)
                    "point": float(parsed_response['data'][4]),  # SYMBOL_POINT (Double)
                    "tick_size": float(parsed_response['data'][5]),  # SYMBOL_TRADE_TICK_SIZE (Double)
                    "tick_value": float(parsed_response['data'][6]),  # SYMBOL_TRADE_TICK_VALUE (Double)
                    "swap_long": float(parsed_response['data'][7]),  # SYMBOL_SWAP_LONG (Double)
                    "swap_short": float(parsed_response['data'][8]),  # SYMBOL_SWAP_SHORT (Double)
                    "stop_level": int(parsed_response['data'][9]),  # SYMBOL_TRADE_STOPS_LEVEL (Integer)
                    "contract_size": float(parsed_response['data'][10])  # SYMBOL_TRADE_CONTRACT_SIZE (Double)
                }
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get instrument info: {error}")

    async def check_terminal_server_connection(self) -> bool:
        """
        Checks if the MT4/5 terminal is connected to the broker server.

        :return: True if connected, otherwise False.
        """
        message = self.make_message('F011', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F011')
            return parsed_response is not None and parsed_response['data'][0] == '1'
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to check terminal server connection: {error}")

    async def check_terminal_type(self) -> Optional[str]:
        """
        Checks the type of the MT terminal (MT4 or MT5).

        :return: 'MT4' or 'MT5' if successful, otherwise None.
        """
        message = self.make_message('F012', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F012')
            if parsed_response:
                return 'MT4' if parsed_response['data'][0] == '1' else 'MT5'
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to check terminal type: {error}")

    async def check_license(self) -> Optional[str]:
        """
        Checks the license type of the MT terminal.

        :return: 'Demo' or 'Licensed' if successful, otherwise None.
        """
        message = self.make_message('F006', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F006')
            if parsed_response:
                return parsed_response['data'][2]
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to check license: {error}")

    async def check_trading_allowed(self, instrument_name: str = 'EURUSD') -> bool:
        """
        Checks if trading is allowed for a specific instrument.

        :param instrument_name: The name of the instrument.
        :return: True if trading is allowed, otherwise False.
        """
        message = self.make_message('F008', '2', [instrument_name])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F008')
            return parsed_response is not None and parsed_response['data'][1] == 'OK'
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to check trading allowed: {error}")

    async def get_instruments(self) -> Optional[List[str]]:
        """
        Retrieves the list of instruments available in the broker's market watch.

        :return: A list of instrument names if successful, otherwise None.
        """
        message = self.make_message('F007', '2', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F007')
            if parsed_response:
                return parsed_response['data'][1:]
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get instruments: {error}")

    async def get_last_x_ticks_from_now(self, instrument_name: str = 'EURUSD', nbrofticks: int = 2000) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves the last x ticks from an instrument.

        :param instrument_name: The name of the instrument.
        :param nbrofticks: The number of ticks to retrieve.
        :return: A list of tick data if successful, otherwise None.
        """
        message = self.make_message('F021', '4', [instrument_name, str(nbrofticks)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F021')
            if parsed_response:
                ticks = []
                for tick in parsed_response['data']:
                    tick_data = tick.split('$')
                    ticks.append({
                        "date": int(tick_data[0]),
                        "ask": float(tick_data[1]),
                        "bid": float(tick_data[2]),
                        "last": float(tick_data[3]),
                        "volume": int(tick_data[4])
                    })
                return ticks
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get last x ticks: {error}")

    async def get_actual_bar_info(self, instrument_name: str = 'EURUSD', timeframe: int = 16408) -> Optional[Dict[str, Any]]:
        """
        Retrieves the last actual bar information for a specific instrument and timeframe.

        :param instrument_name: The name of the instrument.
        :param timeframe: The timeframe in MT5 format.
        :return: A dictionary containing the bar information if successful, otherwise None.
        """
        message = self.make_message('F041', '3', [instrument_name, str(timeframe)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F041')
            if parsed_response:
                return {
                    "instrument": instrument_name,
                    "date": int(parsed_response['data'][0]),
                    "open": float(parsed_response['data'][1]),
                    "high": float(parsed_response['data'][2]),
                    "low": float(parsed_response['data'][3]),
                    "close": float(parsed_response['data'][4]),
                    "volume": int(parsed_response['data'][5])
                }
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get actual bar info: {error}")

    async def get_specific_bar(self, instrument_list: List[str], specific_bar_index: int = 1, timeframe: int = 16408) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves information for a specific bar for a list of instruments.

        :param instrument_list: A list of instrument names.
        :param specific_bar_index: The index of the specific bar.
        :param timeframe: The timeframe in MT5 format.
        :return: A list of dictionaries containing the bar information if successful, otherwise None.
        """
        instruments = '$'.join(instrument_list)
        message = self.make_message('F045', '3', [instruments, str(specific_bar_index), str(timeframe)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F045')
            if parsed_response:
                bars = []
                for bar in parsed_response['data']:
                    bar_data = bar.split('$')
                    bars.append({
                        "instrument": bar_data[0],
                        "date": int(bar_data[1]),
                        "open": float(bar_data[2]),
                        "high": float(bar_data[3]),
                        "low": float(bar_data[4]),
                        "close": float(bar_data[5]),
                        "volume": int(bar_data[6])
                    })
                return bars
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get specific bar info: {error}")

    async def get_last_x_bars_from_now(self, instrument_name: str = 'EURUSD', timeframe: int = 16408, nbrofbars: int = 1000) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves the last x bars from an instrument.

        :param instrument_name: The name of the instrument.
        :param timeframe: The timeframe in MT5 format.
        :param nbrofbars: The number of bars to retrieve.
        :return: A list of bar data if successful, otherwise None.
        """
        message = self.make_message('F042', '5', [instrument_name, str(timeframe), '0', str(nbrofbars)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F042')
            if parsed_response:
                bars = []
                for bar in parsed_response['data']:
                    bar_data = bar.split('$')
                    bars.append({
                        "date": int(bar_data[0]),
                        "open": float(bar_data[1]),
                        "high": float(bar_data[2]),
                        "low": float(bar_data[3]),
                        "close": float(bar_data[4]),
                        "volume": int(bar_data[5])
                    })
                return bars
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get last x bars: {error}")

    async def get_all_open_positions(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves all open positions.

        :return: A list of dictionaries containing open position information if successful, otherwise None.
        """
        message = self.make_message('F061', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F061')
            if parsed_response:
                positions = []
                for position in parsed_response['data']:
                    position_data = position.split('$')
                    positions.append({
                        "ticket": int(position_data[0]),
                        "instrument": position_data[1],
                        "order_ticket": int(position_data[2]),
                        "position_type": position_data[3],
                        "magic_number": int(position_data[4]),
                        "volume": float(position_data[5]),
                        "open_price": float(position_data[6]),
                        "open_time": int(position_data[7]),
                        "stop_loss": float(position_data[8]),
                        "take_profit": float(position_data[9]),
                        "comment": position_data[10],
                        "profit": float(position_data[11]),
                        "swap": float(position_data[12]),
                        "commission": float(position_data[13])
                    })
                return positions
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get all open positions: {error}")

    async def get_all_closed_positions(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves all closed positions.

        :return: A list of dictionaries containing closed position information if successful, otherwise None.
        """
        message = self.make_message('F063', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F063')
            if parsed_response:
                positions = []
                for position in parsed_response['data']:
                    position_data = position.split('$')
                    positions.append({
                        "ticket": int(position_data[0]),
                        "instrument": position_data[1],
                        "order_ticket": int(position_data[2]),
                        "position_type": position_data[3],
                        "magic_number": int(position_data[4]),
                        "volume": float(position_data[5]),
                        "open_price": float(position_data[6]),
                        "open_time": int(position_data[7]),
                        "stop_loss": float(position_data[8]),
                        "take_profit": float(position_data[9]),
                        "close_price": float(position_data[10]),
                        "close_time": int(position_data[11]),
                        "comment": position_data[12],
                        "profit": float(position_data[13]),
                        "swap": float(position_data[14]),
                        "commission": float(position_data[15])
                    })
                return positions
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get all closed positions: {error}")

    async def get_all_deleted_orders(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves all deleted orders.

        :return: A list of dictionaries containing deleted order information if successful, otherwise None.
        """
        message = self.make_message('F065', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F065')
            if parsed_response:
                orders = []
                for order in parsed_response['data']:
                    order_data = order.split('$')
                    orders.append({
                        "ticket": int(order_data[0]),
                        "instrument": order_data[1],
                        "order_type": order_data[2],
                        "magic_number": int(order_data[3]),
                        "volume": float(order_data[4]),
                        "open_price": float(order_data[5]),
                        "open_time": int(order_data[6]),
                        "stop_loss": float(order_data[7]),
                        "take_profit": float(order_data[8]),
                        "delete_price": float(order_data[9]),
                        "delete_time": int(order_data[10]),
                        "comment": order_data[11]
                    })
                return orders
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get all deleted orders: {error}")

    async def open_order(self, instrument_name: str, order_type: str, volume: float, open_price: float, slippage: int, magic_number: int, stop_loss: float, take_profit: float, comment: str, market: bool) -> Optional[int]:
        """
        Opens a new order.

        :param instrument_name: The name of the instrument.
        :param order_type: The type of the order (e.g., 'buy', 'sell').
        :param volume: The volume of the order.
        :param open_price: The open price of the order.
        :param slippage: The slippage value.
        :param magic_number: The magic number for the order.
        :param stop_loss: The stop loss value.
        :param take_profit: The take profit value.
        :param comment: The comment for the order.
        :param market: Whether the order is a market order.
        :return: The ticket number of the opened order if successful, otherwise None.
        """
        message = self.make_message('F070', '9', [instrument_name, order_type, str(volume), str(open_price), str(slippage), str(magic_number), str(stop_loss), str(take_profit), comment, str(market)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F070')
            if parsed_response:
                return int(parsed_response['data'][0])
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to open order: {error}")

    async def close_position_by_ticket(self, ticket: int) -> bool:
        """
        Closes a position by its ticket number.

        :param ticket: The ticket number of the position.
        :return: True if the position was closed successfully, otherwise False.
        """
        message = self.make_message('F071', '2', [str(ticket)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F071')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to close position by ticket: {error}")

    async def close_position_partial_by_ticket(self, ticket: int, volume_to_close: float) -> bool:
        """
        Closes a position partially by its ticket number.

        :param ticket: The ticket number of the position.
        :param volume_to_close: The volume to close.
        :return: True if the position was partially closed successfully, otherwise False.
        """
        message = self.make_message('F072', '3', [str(ticket), str(volume_to_close)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F072')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to close position partially by ticket: {error}")

    async def delete_order_by_ticket(self, ticket: int) -> bool:
        """
        Deletes an order by its ticket number.
        """
        message = self.make_message('F073', '2', [str(ticket)])
        self.return_error = ''
        
        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F073')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to delete order by ticket: {error}")

    async def get_all_pending_orders(self) -> Optional[List[Dict[str, Any]]]:
        message = self.make_message('F060', '1', [])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F060')
            if parsed_response:
                orders = []
                for order in parsed_response['data']:
                    order_data = order.split('$')
                    orders.append({
                        "ticket": int(order_data[0]),
                        "instrument": order_data[1],
                        "order_type": order_data[2],
                        "magic_number": int(order_data[3]),
                        "volume": float(order_data[4]),
                        "open_price": float(order_data[5]),
                        "stop_loss": float(order_data[6]),
                        "take_profit": float(order_data[7]),
                        "comment": order_data[8]
                    })
                return orders
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get all pending orders: {error}")

    async def get_all_closed_positions_within_window(self, date_from: datetime, date_to: datetime) -> Optional[List[Dict[str, Any]]]:
        message = self.make_message('F062', '3', [date_from.strftime('%Y/%m/%d/%H/%M/%S'), date_to.strftime('%Y/%m/%d/%H/%M/%S')])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F062')
            if parsed_response:
                positions = []
                for position in parsed_response['data']:
                    position_data = position.split('$')
                    positions.append({
                        "ticket": int(position_data[0]),
                        "instrument": position_data[1],
                        "order_type": position_data[2],
                        "magic_number": int(position_data[3]),
                        "volume": float(position_data[4]),
                        "open_price": float(position_data[5]),
                        "open_time": int(position_data[6]),
                        "stop_loss": float(position_data[7]),
                        "take_profit": float(position_data[8]),
                        "close_price": float(position_data[9]),
                        "close_time": int(position_data[10]),
                        "comment": position_data[11],
                        "profit": float(position_data[12]),
                        "swap": float(position_data[13]),
                        "commission": float(position_data[14])
                    })
                return positions
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get all closed positions within window: {error}")

    async def get_all_deleted_pending_orders_within_window(self, date_from: datetime, date_to: datetime) -> Optional[List[Dict[str, Any]]]:
        message = self.make_message('F064', '3', [date_from.strftime('%Y/%m/%d/%H/%M/%S'), date_to.strftime('%Y/%m/%d/%H/%M/%S')])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F064')
            if parsed_response:
                orders = []
                for order in parsed_response['data']:
                    order_data = order.split('$')
                    orders.append({
                        "ticket": int(order_data[0]),
                        "instrument": order_data[1],
                        "order_type": order_data[2],
                        "magic_number": int(order_data[3]),
                        "volume": float(order_data[4]),
                        "open_price": float(order_data[5]),
                        "open_time": int(order_data[6]),
                        "stop_loss": float(order_data[7]),
                        "take_profit": float(order_data[8]),
                        "delete_price": float(order_data[9]),
                        "delete_time": int(order_data[10]),
                        "comment": order_data[11]
                    })
                return orders
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get all deleted pending orders within window: {error}")

    async def closeby_position_by_ticket(self, ticket: int, opposite_ticket: int) -> bool:
        message = self.make_message('F074', '3', [str(ticket), str(opposite_ticket)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F074')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to close position by opposite position: {error}")

    async def close_positions_async(self, instrument_name: str = '***', magic_number: int = -1) -> bool:
        message = self.make_message('F091', '3', [instrument_name, str(magic_number)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F091')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to close positions async: {error}")

    async def set_sl_and_tp_for_position(self, ticket: int, stop_loss: float, take_profit: float) -> bool:
        message = self.make_message('F075', '4', [str(ticket), str(stop_loss), str(take_profit)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F075')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to set SL and TP for position: {error}")

    async def set_sl_and_tp_for_pending_order(self, ticket: int, stop_loss: float, take_profit: float) -> bool:
        message = self.make_message('F076', '4', [str(ticket), str(stop_loss), str(take_profit)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F076')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to set SL and TP for pending order: {error}")

    async def reset_sl_and_tp_for_position(self, ticket: int) -> bool:
        message = self.make_message('F077', '2', [str(ticket)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F077')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to reset SL and TP for position: {error}")

    async def reset_sl_and_tp_for_pending_order(self, ticket: int) -> bool:
        message = self.make_message('F078', '2', [str(ticket)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F078')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to reset SL and TP for pending order: {error}")

    async def change_settings_for_pending_order(self, ticket: int, price: float, stop_loss: float, take_profit: float) -> bool:
        message = self.make_message('F079', '5', [str(ticket), str(price), str(stop_loss), str(take_profit)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F079')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to change settings for pending order: {error}")

    async def set_global_variable(self, global_name: str, global_value: float) -> bool:
        message = self.make_message('F080', '3', [global_name, str(global_value)])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F080')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to set global variable: {error}")

    async def get_global_variable(self, global_name: str) -> Optional[float]:
        message = self.make_message('F081', '2', [global_name])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return None

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F081')
            if parsed_response:
                return float(parsed_response['data'][0])
            return None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to get global variable: {error}")

    async def switch_auto_trading_on_off(self, on_off: bool) -> bool:
        message = self.make_message('F084', '2', ['On' if on_off else 'Off'])
        self.return_error = ''

        try:
            response = await self.send_message(message)
            if not response:
                self.ok = False
                return False

            if self.debug:
                print(response)

            parsed_response = self._process_response(response, 'F084')
            return parsed_response is not None
        except Exception as error:
            self.return_error = ERROR_DICT['00001']
            self.ok = False
            raise Exception(f"Failed to switch auto trading on/off: {error}")
