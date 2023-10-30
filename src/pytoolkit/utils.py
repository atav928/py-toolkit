"""Utilities."""

from enum import Enum
import os
from pathlib import Path
import pwd
import socket
from typing import Any, Generator, List, MutableMapping, Union
import base64
import re
import yaml

from pytoolkit.static import ENCODING


def verify_list(value: Any) -> List[str]:
    """
    Verify value being passed is a list or split out a comma seperted string into a list.

    :param value: Original value. Should be a str|list
    :type value: Any
    :raises ValueError: If value is not a string or list
    :return: _description_
    :rtype: List[str]
    """
    if not isinstance(value, list) and isinstance(value, str):
        return value.split(',')
    if isinstance(value, list):
        return value  # type: ignore
    raise ValueError(f"Invalid value {value}")


def convert_to_base64(filename: str) -> bytes:
    """
    Converts a file to a byte string off base64.

    :param filename: Filename
    :type filename: str
    :return: Encoded File String.
    :rtype: base64
    """
    with open(filename, 'rb') as file:
        my_string: bytes = base64.b64decode(file.read())
    return my_string

# Enumerator type


def enum(*sequential, **named) -> type[Enum]:
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict(((v, k) for (k, v) in enums.items()))
    enums["reverse_mapping"] = reverse
    return type("Enum", (), enums)


def isstring(arg):
    try:
        return isinstance(arg, basestring)
    except NameError:
        return isinstance(arg, str) or isinstance(arg, bytes)

# Convenience methods used internally by module
# Do not use these methods outside the module


def string_or_list(value: Any, delimeters: str=None) -> list[str]:
    """
    Return a list containing value.

    This method allows flexibility in class __init__ arguments,
    allowing you to pass a string, object, list, or tuple.
    In all cases, a list will be returned.

    :param value: a string, object, list, or tuple
    :type value: str|obj|list|tuple
    :param delimeter: use a delimeter in the string using pipe(|) as an OR for multiple.
     (Optional) Default no delimeter used. Example: delimeters=',| |;|'
    :type delimeter: str|None
    :return: list
    :rtype: list[str]

    :examples:
        "string" -> [string]
        ("t1", "t2") -> ["t1", "t2"]
        ["l1", "l2"] -> ["l1", "l2"]
        None -> None
    """
    if value is None:
        return None  # type: ignore
    if isstring(value):
        return re.split(delimeters,value,flags=re.IGNORECASE) if delimeters else [value]
    return (list(value) if "__iter__" in dir(value) else [value,])


def reformat_exception(error: Exception) -> str:
    """
    Reformates Exception to print out as a string pass for logging.

    :param error: caught excpetion
    :type error: Exception
    :return: error as string
    :rtype: str
    """
    resp: str = f"{type(error).__name__}: {str(error)}" if error else ""
    # Replacing [ ] with list() due to issues with reading that format with some systems.
    resp = re.sub(r"\'", "", resp)
    resp = re.sub(r'\[', 'list(', resp)
    resp = re.sub(r"\]", ')', resp)
    return resp


def return_filelines(filename: str) -> list[str]:
    """
    Return list of strings in a file.

    :param filename: _description_
    :type filename: str
    :return: _description_
    :rtype: list[str]
    """
    filelines: list[str] = []
    with open(filename, 'r', encoding=ENCODING) as fil:
        filelines = fil.readlines()
    return filelines


def check_file(filename: str) -> str:
    """Check that filename exists and returns Pathlib object if does.

    :param filename: Name of file; full path
    :type filename: str
    :raises FileExistsError: _description_
    :return: File location
    :rtype: Path
    """
    file: Path = Path(filename)
    if not file.exists():
        raise FileExistsError(f"Filename does not exist: {str(filename)}")
    return filename

def return_username(log:Any=None) -> Union[str,None]:
    """
    Return Username Information.

    :param log: logger, defaults to None
    :type log: Logger, optional
    :return: username
    :rtype: Union[str,None]
    """
    try:
        return pwd.getpwuid(os.getuid())[0]
    except Exception as err:
        error: str = reformat_exception(err)
        if log:
            log.error(f"msg=\"Unable to get username\"|{error=}")
    return None

def return_hostinfo(fqdn:bool=True) -> str:
    """
    Return Hostname information on system.

    :param fqdn: Retun FQDN or Hostname, defaults to True
    :type fqdn: bool, optional
    :return: System Hostname/FQDN
    :rtype: str
    """
    if fqdn:
        return socket.getfqdn()
    return socket.gethostname()

def _flatten_dict_gen(_d: MutableMapping[str,Any], parent_key: str,
                      sep:str,extended_label:bool,
                      skip_item:Union[list[str],None]) -> Generator[tuple[str, Any], Any, None]:
    for k,v in _d.items():
        if extended_label:
            new_key: str = parent_key + sep + k if parent_key and k not in skip_item else k # type: ignore
        else:
            new_key: str = k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v,new_key,sep=sep).items()  # type: ignore
        else:
            yield new_key,v

def flatten_dict(_dict: MutableMapping[str,Any], parent_key: str="",
                 sep: str=".", extended_label: bool=False,
                 skip_item: Union[list[str],None] = None) -> dict[str,Any]:
    """
    Flatten out a dictionary with nested values.

    :param _dict: Dictionary
    :type _dict: MutableMapping[str,Any]
    :param parent_key: Top Level Key, defaults to ""
    :type parent_key: str, optional
    :param sep: Seperator, defaults to "."
    :type sep: str, optional
    :param extended_label: Uses the same key by default or appends the hierarchy
     into the name of the key used to express the nesting structure, defaults to False
    :type extended_label: bool, optional
    :param skip_item: _description_, defaults to []
    :type skip_item: list, optional
    :return: Flattened Dictionary
    :rtype: dict[str,Any]
    """
    return dict(_flatten_dict_gen(_dict,parent_key,sep,extended_label,skip_item))

def read_yaml(filename: Path) -> dict[str,Any]:
    """
    Read in a YAML configuration file.

    :param filename: Yaml File Full Path
    :type filename: Path
    :return: Yaml Configurations
    :rtype: dict[str,Any]
    """
    with open(filename,'r', encoding=ENCODING) as r_yaml:
        settings = yaml.safe_load(r_yaml)
    return settings
