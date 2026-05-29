import datetime
import json
import math

from temparse import Conversion, FormatConversion, parse


def test_str():
    (r,) = parse[str](t'"{str}"?', '"teststr"?')
    assert r == "teststr"


def test_int():
    (r,) = parse[int](t"x = {int}", "x = +31")
    assert r == 31

    (r,) = parse[int](t"x = {int:16}", "x = ff")
    assert r == 255

    (r,) = parse[int](t"x = {int}", "x = 0xff")
    assert r == 255


def test_float():
    (r,) = parse[float](t"Pi = {float}", "Pi = 3.1415926")
    assert r == 3.1415926

    (r,) = parse[float](t"x = {float}", "x = 3")
    assert r == 3

    (r,) = parse[float](t"x = {float}", "x = nan")
    assert math.isnan(r)

    (r,) = parse[float](t"x = {float}", "x = -INF")
    assert math.isinf(r)


def test_complex():
    (r,) = parse[complex](t"x = {complex}", "x = -1.23+4.5j")
    assert r == (-1.23 + 4.5j)


def test_json():
    (r,) = parse[list[int]](t"result is {json}", "result is [1, 2, 3]")
    assert r == [1, 2, 3]

    (r,) = parse[dict[str, int | str]](
        t"result is {json}",
        'result is {"a": 1, "b": "abc"}',
    )
    assert r == {"a": 1, "b": "abc"}


def test_datetime():
    (r,) = parse[datetime.datetime](
        t"Now is {datetime.datetime:%d/%m/%y %H:%M:%S.%f}",
        "Now is 31/01/22 23:59:59.999999",
    )
    assert r == datetime.datetime(2022, 1, 31, 15, 59, 59, 999999, tzinfo=datetime.UTC)


def test_date():
    (r,) = parse[datetime.date](t"Now is {datetime.date:%m/%d;%Y}", "Now is 02/29;1984")
    assert r == datetime.date(1984, 2, 29)

    (r,) = parse[datetime.date](t"{datetime.date:%Y/%j}", "2023/9")
    assert r == datetime.date(2023, 1, 9)

    (r,) = parse[datetime.date](t"{datetime.date:%Y/%j}", "2023/009")
    assert r == datetime.date(2023, 1, 9)


def test_time():
    (r,) = parse[datetime.time](t"a {datetime.time:%H:%M:%S} b", "a 13:23:27 b")
    assert r == datetime.time(13, 23, 27)


def test_conv():
    @Conversion
    def conv(s: str) -> int:
        return 0

    (r,) = parse[int](t"a {conv} b", "a xyz b")
    assert r == 0


def test_format_conv():
    @FormatConversion
    def conv(s: str, spec: str) -> str:
        lo, hi = spec.split(",")
        return s[int(lo) : int(hi)]

    (result,) = parse[str](t"{conv:2,5}", "abcdefg")
    assert result == "cde"
