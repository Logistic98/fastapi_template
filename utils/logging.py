# -*- coding: utf-8 -*-

import sys
import os
import datetime
import re
from typing import Any, Dict, List, Union
from copy import deepcopy
from asyncio import Lock
import aiofiles


class Styles(object):
    CLEAR = 0; BOLD = 1; BOLD_RESET = 22; FAINT = 2; FAINT_RESET = 22
    ITALIC = 3; ITALIC_RESET = 23; UNDERLINE = 4; UNDERLINE_RESET = 24
    BLINK = 5; BLINK_RESET = 25; REVERSE = 7; REVERSE_RESET = 27
    INVISIBLE = 8; INVISIBLE_RESET = 28; STRIKE = 9; STRIKE_RESET = 29
    DEFAULT = 39; DEFAULT_BG = 49
    BLACK = 30; BLACK_BG = 40; RED = 31; RED_BG = 41; GREEN = 32; GREEN_BG = 42
    YELLOW = 33; YELLOW_BG = 43; BLUE = 34; BLUE_BG = 44; MAGENTA = 35; MAGENTA_BG = 45
    CYAN = 36; CYAN_BG = 46; WHITE = 37; WHITE_BG = 47
    BRIGHT_BLACK = 90; BRIGHT_BLACK_BG = 100; BRIGHT_RED = 91; BRIGHT_RED_BG = 101
    BRIGHT_GREEN = 92; BRIGHT_GREEN_BG = 102; BRIGHT_YELLOW = 93; BRIGHT_YELLOW_BG = 103
    BRIGHT_BLUE = 94; BRIGHT_BLUE_BG = 104; BRIGHT_MAGENTA = 95; BRIGHT_MAGENTA_BG = 105
    BRIGHT_CYAN = 96; BRIGHT_CYAN_BG = 106; BRIGHT_WHITE = 97; BRIGHT_WHITE_BG = 107

    @staticmethod
    def ID_COLOR(id): return f"38;5;{id}"
    @staticmethod
    def ID_COLOR_BG(id): return f"48;5;{id}"
    @staticmethod
    def RGB_COLOR(r,g,b): return f"38;2;{r};{g};{b}"
    @staticmethod
    def RGB_COLOR_BG(r,g,b): return f"48;2;{r};{g};{b}"
    @staticmethod
    def make_color_prefix(code): return f"\x1b[{code}m"
    @staticmethod
    def make_colors_prefix(codes: List[Any] = []):
        return ''.join([Styles.make_color_prefix(code) for code in codes])


class Styled(object):
    def __init__(self, data: Any = "", *styles: Any):
        self.plain_str = data.plain_str if isinstance(data, Styled) else str(data)
        splited_str = re.split(r'(\{\{*[\w\W]*?\}*\})', str(data))
        self.styled_str = Styles.make_color_prefix(Styles.CLEAR) + ''.join(
            [(Styles.make_colors_prefix(styles) + s) if i % 2 == 0 else s for i, s in enumerate(splited_str)]
        ) + Styles.make_color_prefix(Styles.CLEAR)

    def __add__(self, other):
        g = Styled()
        if isinstance(other, Styled):
            g.plain_str = self.plain_str + other.plain_str
            g.styled_str = self.styled_str + other.styled_str
        else:
            g.plain_str = self.plain_str + str(other)
            g.styled_str = self.styled_str + str(other)
        return g

    __radd__ = __add__

    def __iadd__(self, other):
        if isinstance(other, Styled):
            self.plain_str += other.plain_str
            self.styled_str += other.styled_str
        else:
            self.plain_str += str(other)
            self.styled_str += str(other)
        return self

    @property
    def plain(self) -> str: return self.plain_str
    @property
    def styled(self) -> str: return self.styled_str
    def __str__(self) -> str: return self.styled_str

    def format(self, *args, **kwargs):
        g = Styled()
        args_plain = [a.plain if isinstance(a, Styled) else str(a) for a in args]
        kwargs_plain = {k:(v.plain if isinstance(v, Styled) else str(v)) for k,v in kwargs.items()}
        args_styled = [a.styled if isinstance(a, Styled) else str(a) for a in args]
        kwargs_styled = {k:(v.styled if isinstance(v, Styled) else str(v)) for k,v in kwargs.items()}
        g.plain_str = self.plain_str.format(*args_plain, **kwargs_plain)
        g.styled_str = self.styled_str.format(*args_styled, **kwargs_styled)
        return g


class Levels(object):
    DEBUG=0; INFO=1; NOTICE=2; WARNING=3; ERROR=4; CRITICAL=5


class LoggerConfig(object):
    DEFAULT_CONFIG = {
        "print": {
            "enabled": True, "colored": True, "log_level": Levels.DEBUG,
            "time": {"enabled": True, "time_format": "%Y-%m-%d %H:%M:%S",
                     "time_styles": [Styles.BRIGHT_BLACK], "time_quote_format": "[{}]", "time_quote_styles": []},
            "level": {"enabled": True, "levels": {
                str(Levels.DEBUG): {"text":"D","styles":[Styles.BRIGHT_BLACK]},
                str(Levels.INFO): {"text":"I","styles":[]},
                str(Levels.NOTICE): {"text":"N","styles":[Styles.BOLD]},
                str(Levels.WARNING): {"text":"W","styles":[Styles.YELLOW]},
                str(Levels.ERROR): {"text":"E","styles":[Styles.RED]},
                str(Levels.CRITICAL): {"text":"C","styles":[Styles.RED,Styles.BOLD,Styles.BLINK]}
            }}
        },
        "file": {
            "enabled": False, "colored": False, "log_level": Levels.DEBUG,
            "log_root_path": "./logs", "log_name": "log.", "log_suffix": "txt",
            "log_append_time": True, "log_time_format": "%Y-%m-%d",
            "flush_every_n_logs": 0,
            "time": {"enabled": True, "time_format": "%Y-%m-%d %H:%M:%S",
                     "time_styles": [Styles.BRIGHT_BLACK], "time_quote_format": "[{}]", "time_quote_styles": []},
            "level": {"enabled": True, "levels": {
                str(Levels.DEBUG): {"text":"DEBUG","styles":[Styles.BRIGHT_BLACK]},
                str(Levels.INFO): {"text":"INFO","styles":[]},
                str(Levels.NOTICE): {"text":"NOTICE","styles":[Styles.BOLD]},
                str(Levels.WARNING): {"text":"WARN","styles":[Styles.YELLOW]},
                str(Levels.ERROR): {"text":"ERROR","styles":[Styles.RED]},
                str(Levels.CRITICAL): {"text":"CRIT","styles":[Styles.RED,Styles.BOLD,Styles.BLINK]}
            }}
        }
    }


class Logger(object):
    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        self.config = deepcopy(LoggerConfig.DEFAULT_CONFIG if config is None else config)
        self.config = {**self.config, **kwargs}
        if self.config.get("file", {}).get("enabled", False):
            os.makedirs(self.config["file"].get("log_root_path", "./logs"), exist_ok=True)
        self.log_buffer = []
        self._lock = Lock()

    async def log(self, level: Levels, text: Union[Styled, Any], *args, **kwargs):
        text = Styled(text)
        if args or kwargs:
            text = text.format(*args, **kwargs)
        if self.config["print"]["enabled"] and level >= self.config["print"]["log_level"]:
            prefix = self._make_prefix_s(level, "print")
            ostr = f"{str(prefix) if self.config['print']['colored'] else prefix.plain}" \
                   f"{str(text) if self.config['print']['colored'] else text.plain}"
            (sys.stdout if level < Levels.ERROR else sys.stderr).write(ostr + "\n")
            (sys.stdout if level < Levels.ERROR else sys.stderr).flush()

        if self.config["file"]["enabled"] and level >= self.config["file"]["log_level"]:
            prefix = self._make_prefix_s(level, "file")
            ostr = f"{str(prefix) if self.config['file']['colored'] else prefix.plain}" \
                   f"{str(text) if self.config['file']['colored'] else text.plain}"
            async with self._lock:
                self.log_buffer.append(ostr)
                await self._flush_now()

    async def debug(self, text: Union[Styled, Any], *args, **kwargs):   await self.log(Levels.DEBUG, text, *args, **kwargs)
    async def info(self, text: Union[Styled, Any], *args, **kwargs):    await self.log(Levels.INFO, text, *args, **kwargs)
    async def notice(self, text: Union[Styled, Any], *args, **kwargs):  await self.log(Levels.NOTICE, text, *args, **kwargs)
    async def warning(self, text: Union[Styled, Any], *args, **kwargs): await self.log(Levels.WARNING, text, *args, **kwargs)
    async def error(self, text: Union[Styled, Any], *args, **kwargs):   await self.log(Levels.ERROR, text, *args, **kwargs)
    async def critical(self, text: Union[Styled, Any], *args, **kwargs):await self.log(Levels.CRITICAL, text, *args, **kwargs)

    def _make_time_s(self, source="print"):
        tcfg = self.config[source]["time"]
        return Styled(tcfg["time_quote_format"], *tcfg["time_quote_styles"]).format(
            Styled(datetime.datetime.now().strftime(tcfg["time_format"]), *tcfg["time_styles"])
        )

    def _make_level_s(self, level, source="print"):
        lcfg = self.config[source]["level"]["levels"][str(level)]
        return Styled(lcfg["text"], *lcfg["styles"])

    def _make_prefix_s(self, level, source="print", sep=" "):
        scfg = self.config[source]
        return Styled("{}{}{}{}").format(
            self._make_time_s(source) if scfg["time"]["enabled"] else '',
            sep,
            self._make_level_s(level, source) if scfg["level"]["enabled"] else '',
            sep
        )

    async def _flush_now(self):
        if not self.log_buffer: return
        fcfg = self.config["file"]
        fpath = "{}/{}{}.{}".format(
            fcfg["log_root_path"], fcfg["log_name"],
            datetime.datetime.now().strftime(fcfg["log_time_format"]) if fcfg["log_append_time"] else '',
            fcfg["log_suffix"]
        )
        try:
            async with aiofiles.open(fpath, "a", encoding="utf-8") as f:
                for line in self.log_buffer:
                    await f.write(line + "\n")
            self.log_buffer.clear()
        except Exception as e:
            sys.stderr.write(f"[logger] flush failed: {e}\n")
