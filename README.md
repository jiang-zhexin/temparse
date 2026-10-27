# temparse

**temparse = template + parse**, parse strings using t-string templates.

Inspired by [parse](https://github.com/r1chardj0n3s/parse), but built on Python
3.14's [t-strings](https://peps.python.org/pep-0750/), with better type hints.

## Installation

### uv

```bash
uv add temparse
```

### pip

```bash
# Requires Python >= 3.14.
pip install temparse
```

## Quick Start

```python
from temparse import parse

city, year = parse[str, int](
    t"I live in {str}, since {int}", "I live in Tokyo, since 2010"
)
assert city == "Tokyo"
assert year == 2010
```

The return type is `tuple[str, int]`.

## Supported Types

| Interpolation                           | Example               | Output       |
| --------------------------------------- | --------------------- | ------------ |
| `{str}`                                 | `"hello"`             | `"hello"`    |
| `{int}`                                 | `"42"`                | `42`         |
| `{int}`                                 | `"0xff"`              | `255`        |
| `{int:16}`                              | `"ff"`                | `255`        |
| `{float}`                               | `"3.14"`              | `3.14`       |
| `{complex}`                             | `"-1.23+4.5j"`        | `-1.23+4.5j` |
| `{list}`                                | `'[1,2,3]'`           | `[1, 2, 3]`  |
| `{dict}`                                | `'{"a":1}'`           | `{"a": 1}`   |
| `{json}`                                | `'{"a":1}'`           | `{"a": 1}`   |
| `{datetime.datetime:%d/%m/%y %H:%M:%S}` | `"31/01/22 23:59:59"` | `datetime`   |
| `{datetime.date:%Y-%m-%d}`              | `"2024-03-15"`        | `date`       |
| `{datetime.time:%H:%M:%S}`              | `"13:23:27"`          | `time`       |

> [!IMPORTANT]
> list and dict are just aliases for json.

## Custom Conversions

Decorate a function with `@Conversion` to use it directly in a template:

```python
from temparse import Conversion, parse


@Conversion
def percent(s: str) -> float:
    return float(s.rstrip("%")) / 100


(result,) = parse[float](t"x = {percent}", "x = 30%")
assert result == 0.3
```

When your converter needs the format spec as well, use `FormatConversion`:

```python
from temparse import FormatConversion, parse


@FormatConversion
def between(s: str, spec: str) -> str:
    lo, hi = spec.split(",")
    return s[int(lo) : int(hi)]


(result,) = parse[str](t"{between:2,5}", "abcdefg")
assert result == "cde"
```

## `Parser` (Compiled Templates)

Build a parser once and reuse it:

```python
from temparse import Parser

parser = Parser[str, int, float](t"{str} + {int} = {float}")

assert parser.parse("foo + 3 = 3.14") == ("foo", 3, 3.14)
assert parser.parse("bar + 7 = 2.72") == ("bar", 7, 2.72)
```

## `Matcher` (Pattern Matching & Structured Parsing)

Subclass `Matcher` with a `Parser` to match strings in `match/case` statements or parse strings directly into structured instances:

```python
from temparse import Matcher, MatchStr, Parser


class OkResp(Matcher, parser=Parser(t'code={int};message="{str}";')):
    code: int
    message: str


class ErrResp(Matcher, parser=Parser(t'code={int};error="{str}";')):
    code: int
    error: str


def handle_response(raw: str) -> str:
    # Wrap the string with MatchStr to enable pattern matching
    match MatchStr(raw):
        case OkResp(code, message):
            return f"OK ({code}): {message}"
        case ErrResp(code, error):
            return f"Error ({code}): {error}"
        case _:
            return "Unknown response"


assert handle_response('code=200;message="success";') == "OK (200): success"
assert handle_response('code=400;error="bad request";') == "Error (400): bad request"
```

`Matcher` subclasses are also dataclasses that support keyword matching and `.parse()`:

```python
from temparse import Matcher, MatchStr, Parser


class Point(Matcher, parser=Parser(t"x={int}, y={int}")):
    x: int
    y: int


p = Point.parse("x=1, y=2")
assert p == Point(x=1, y=2)

# Wrap the string with MatchStr to enable pattern matching
match MatchStr("x=0, y=5"):
    case Point(x=0, y=y):
        assert y == 5
```

## License

MIT
