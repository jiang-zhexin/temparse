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

| Interpolation                           | Example                  | Output               |
| --------------------------------------- | ------------------------ | -------------------- |
| `{str}`                                 | `"hello"`                | `"hello"`            |
| `{int}`                                 | `"42"`                   | `42`                 |
| `{int}`                                 | `"0xff"`                 | `255`                |
| `{int:16}`                              | `"ff"`                   | `255`                |
| `{float}`                               | `"3.14"`                 | `3.14`               |
| `{complex}`                             | `"-1.23+4.5j"`           | `-1.23+4.5j`         |
| `{json}`                                | `'[1,2,3]'`, `'{"a":1}'` | `[1,2,3]`, `{"a":1}` |
| `{datetime.datetime:%d/%m/%y %H:%M:%S}` | `"31/01/22 23:59:59"`    | `datetime`           |
| `{datetime.date:%Y-%m-%d}`              | `"2024-03-15"`           | `date`               |
| `{datetime.time:%H:%M:%S}`              | `"13:23:27"`             | `time`               |

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

## License

MIT
