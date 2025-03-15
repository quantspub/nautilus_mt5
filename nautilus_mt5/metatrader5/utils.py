"""
Collection of misc tools
"""

import sys
from typing import Union, List


class BadMessage(Exception):
    def __init__(self, text):
        self.text = text


class ClientException(Exception):
    def __init__(self, code, msg, text):
        self.code = code
        self.msg = msg
        self.text = text

def current_fn_name(parent_idx: int = 0) -> str:
    """
    Get the name of the current function.

    Args:
        parent_idx (int): The index of the parent frame. Defaults to 0.

    Returns:
        str: The name of the current function.
    """
    return sys._getframe(1 + parent_idx).f_code.co_name

def parse_mql5_response(text: Union[str, None]) -> Union[str, List[List[str]], None]:
    """
    Parse the MQL5 response text.

    Args:
        text (Union[str, None]): The MQL5 response text.

    Returns:
        Union[str, List[List[str]], None]: The parsed response.
    """
    if text is None:
        return text
    text = text.rstrip(";")
    array = text.split(";")
    result_array = [item.split(",") for item in array]
    if len(array) == 1 and len(result_array[0]) == 1:
        return result_array[0][0]
    return result_array


def get_mql5_period(text: str) -> str:
    """
    Get the MQL5 period string.

    Args:
        text (str): The period text.

    Returns:
        str: The MQL5 period string.
    """
    periods = {
        "M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30",
        "H1", "H2", "H3", "H4", "H6", "H8", "H12", "D1", "W1", "MN1",
    }
    text_upper = text.upper()
    if text_upper in periods:
        return f"PERIOD_{text_upper}"
    return "PERIOD_CURRENT"