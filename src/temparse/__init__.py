import datetime
import functools
import json
import re
from collections.abc import Callable
from string.templatelib import Interpolation, Template
from typing import Any, final, get_origin, is_typeddict

__all__ = ["Conversion", "FormatConversion", "Parser", "parse"]


@final
class Parser[*T]:
    """
    A compiled template parser that can be reused to parse multiple strings.

    example:
    ```python
    parser = Parser[str, int, float](t"{str} + {int} = {float}")

    parser.parse("foo + 3 = 3.14")
    ```
    """

    def __init__(self, template: Template, flags: re.RegexFlag = re.NOFLAG) -> None:
        if len(template.interpolations) == 0:
            raise ValueError("template must contain at least one interpolation")

        self._template = template
        self._flags = flags
        self._expression = "".join(
            re.escape(item) if isinstance(item, str) else r"(.+?)" for item in template
        )

    @functools.cached_property
    def _match_re(self) -> re.Pattern[str]:
        return re.compile(self._expression, self._flags)

    def parse(self, s: str) -> tuple[*T]:
        m = self._match_re.fullmatch(s)
        if m is None:
            raise ValueError(f"invalid format: {s!r}")

        return tuple(
            _convert(text, interpolation)
            for text, interpolation in zip(m.groups(), self._template.interpolations)
        )


@final
class parse[*T]:
    """
    Parse string by template.

    example:
    ```python
    city, year = parse[str, int](
        t"I live in {str}, since {int}", "I live in Tokyo, since 2010"
    )
    assert city == "Tokyo"
    assert year == 2010
    ```
    """

    def __new__(cls, t: Template, s: str, flags: re.RegexFlag = re.NOFLAG) -> tuple[*T]:
        """
        Used to replace this function until [PEP 718](https://peps.python.org/pep-0718/) is accepted.

        ```python
        def parse[*T](t: Template, s: str, flags: re.RegexFlag = re.NOFLAG) -> tuple[*T]:
            return Parser(t).parse(s)
        ```
        """
        return Parser(t, flags).parse(s)


@final
class Conversion[T]:
    """
    Convert the string to your object.

    example:
    ```python
    @Conversion
    def percent(s: str) -> float:
        return float(s.rstrip("%")) / 100


    (result,) = parse[float](t"x = {percent}", "x = 30%")
    assert result == 0.3
    ```
    """

    __name__: str
    __qualname__: str

    def __init__(self, func: Callable[[str], T]) -> None:
        self._convert = func
        functools.update_wrapper(self, func)

    def __call__(self, s: str) -> T:
        return self._convert(s)


@final
class FormatConversion[T]:
    """
    Convert the string to your object with format.

    example:
    ```python
    @FormatConversion
    def between(s: str, spec: str) -> str:
        lo, hi = spec.split(",")
        return s[int(lo) : int(hi)]

    (result,) = parse[str](t"{between:2,5}", "abcdefg")
    assert result == "cde"
    ```
    """

    __name__: str
    __qualname__: str

    def __init__(self, func: Callable[[str, str], T]) -> None:
        self._convert = func
        functools.update_wrapper(self, func)

    def __call__(self, s: str, format: str) -> T:
        return self._convert(s, format)


def _convert(s: str, i: Interpolation[Any]) -> Any:
    origin = get_origin(i.value) or i.value
    match origin:
        case Conversion():
            return i.value(s)

        case FormatConversion():
            return i.value(s, i.format_spec)

        case datetime.datetime:
            return datetime.datetime.strptime(s, i.format_spec).astimezone(datetime.UTC)

        case datetime.date:
            return datetime.date.strptime(s, i.format_spec)

        case datetime.time:
            return datetime.time.strptime(s, i.format_spec)

        case _ if origin is int:
            return int(s, base=int(i.format_spec) if i.format_spec else 0)

        case _ if origin is float:
            return float(s)

        case _ if origin is complex:
            return complex(s)

        case _ if origin is str:
            return s

        case _ if (
            origin is list or origin is dict or origin is json or is_typeddict(origin)
        ):
            return json.loads(s)

        case _:
            raise TypeError(f"unkown object: {i.value}")
