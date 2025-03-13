"""
Collection of misc tools
"""

import sys
import logging
import inspect
from typing import Dict, List, Union


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


class BadMessage(Exception):
    def __init__(self, text):
        self.text = text


class ClientException(Exception):
    def __init__(self, code, msg, text):
        self.code = code
        self.msg = msg
        self.text = text


def current_fn_name(parent_idx=0):
    return sys._getframe(1 + parent_idx).f_code.co_name

class Object:
    def __str__(self):
        return "Object"

    def __repr__(self):
        return f"{id(self)}: {self.__str__()}"


def MQL5parse(text):
    if text is None:
        return text
    text = text[:-1]
    Array = text.split(";")
    resultArray = [i.split(",") for i in Array]
    if len(Array) == 1 and len(resultArray[0]) == 1:
        return resultArray[0][0]
    return resultArray


def MQL5Period(text):
    Periods = [
        "M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30",
        "H1", "H2", "H3", "H4", "H6", "H8", "H12", "D1", "W1", "MN1",
    ]
    text_upper = text.upper()
    if text_upper in Periods:
        return f"PERIOD_{text_upper}"
    return "PERIOD_CURRENT"