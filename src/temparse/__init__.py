import builtins
import dataclasses
import datetime
import functools
import json
import re
from collections.abc import Callable
from string.templatelib import Interpolation, Template
from typing import (
    Any,
    Literal,
    Self,
    cast,
    dataclass_transform,
    final,
    get_origin,
    is_typeddict,
    overload,
)

__all__ = ["Conversion", "FormatConversion", "MatchStr", "Matcher", "Parser", "parse"]


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

    @overload
    def parse(self, s: str, *, return_none: Literal[False] = False) -> tuple[*T]: ...

    @overload
    def parse(self, s: str, *, return_none: bool) -> tuple[*T] | None: ...

    def parse(self, s: str, *, return_none: bool = False) -> tuple[*T] | None:
        m = self._match_re.fullmatch(s)
        if m is None:
            if return_none:
                return None
            raise ValueError(f"invalid format: {s!r}")

        return cast(
            tuple[*T],
            tuple(
                _convert(text, interpolation)
                for text, interpolation in zip(
                    m.groups(), self._template.interpolations
                )
            ),
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
        return Parser[*T](t, flags).parse(s)


@dataclass_transform()
class _MatcherMeta(type):
    _parser: Parser
    __match_args__: tuple[str, ...]

    def __instancecheck__(cls, instance: object) -> bool:
        if super().__instancecheck__(instance):
            return True
        if not isinstance(instance, MatchStr):
            return False

        result = cls._parser.parse(instance, return_none=True)
        if result is None:
            return False

        for k, v in zip(cls.__match_args__, result):
            setattr(instance, k, v)
        return True


class Matcher(metaclass=_MatcherMeta):
    """
    Base class for structural pattern matching and structured template parsing.

    example:
    ```python
    class OkResp(Matcher, parser=Parser(t'code={int};message="{str}";')):
        code: int
        message: str


    class ErrResp(Matcher, parser=Parser(t'code={int};error="{str}";')):
        code: int
        error: str


    match MatchStr('code=400;error="bad request";'):
        case OkResp(code, message):
            print(f"OK ({code}): {message}")
        case ErrResp(code, error):
            print(f"Error ({code}): {error}")
    ```
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def __init_subclass__(cls, parser: Parser) -> None:
        super().__init_subclass__()
        dataclasses.dataclass(cls)
        cls._parser = parser
        if len(cls.__match_args__) != len(parser._template.interpolations):
            raise ValueError("number of fields must match template interpolations")

    @classmethod
    def parse(cls, s: str) -> Self:
        """
        Parse a string using the class's parser and return an instance of the class.

        example:
        ```python
        p = Point.parse("x=1, y=2")
        assert p == Point(x=1, y=2)
        ```
        """
        return cls(*cls._parser.parse(s))


class MatchStr(str):
    """
    A `str` subclass that enables structural pattern matching with `Matcher` subclasses.

    example:
    ```python
    match MatchStr("x=1, y=2"):
        case Point(x, y):
            assert x == 1 and y == 2
    ```
    """

    def __new__(cls, s: str, /) -> Self:
        return super().__new__(cls, s)


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

    def __init__(self, func: Callable[[str, str], T]) -> None:
        self._convert = func
        functools.update_wrapper(self, func)

    def __call__(self, s: str, format: str) -> T:
        return self._convert(s, format)


def _convert(s: str, interp: Interpolation[Any]) -> Any:
    origin = get_origin(interp.value) or interp.value
    match origin:
        case Conversion():
            return interp.value(s)

        case FormatConversion():
            return interp.value(s, interp.format_spec)

        case datetime.datetime:
            return datetime.datetime.strptime(s, interp.format_spec).astimezone(
                datetime.UTC
            )

        case datetime.date:
            return datetime.date.strptime(s, interp.format_spec)

        case datetime.time:
            return datetime.time.strptime(s, interp.format_spec)

        case builtins.int:
            return int(s, base=int(interp.format_spec) if interp.format_spec else 0)

        case builtins.float:
            return float(s)

        case builtins.complex:
            return complex(s)

        case builtins.str:
            return s

        case builtins.list | builtins.dict:
            return json.loads(s)

        case _ if origin is json or is_typeddict(origin):
            return json.loads(s)

        case _:
            raise TypeError(f"unkown object: {interp.value}")
