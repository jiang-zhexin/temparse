import datetime
from typing import TypedDict, assert_type

import pytest

from temparse import Conversion, FormatConversion, Matcher, MatchStr, Parser


class TheX(Matcher, parser=Parser(t"x={int};")):
    x: int


class TheY(Matcher, parser=Parser(t"y={str};")):
    y: str


class ThePoint(Matcher, parser=Parser(t"x={int}; y={str}; z={float}")):
    x: int
    y: str
    z: float


def test_match_positional():
    def match_point(
        point: str,
    ) -> tuple[str, int | str | tuple[int, str, float] | None]:
        match MatchStr(point):
            case TheX(x):
                assert_type(x, int)
                return ("x", x)
            case TheY(y):
                assert_type(y, str)
                return ("y", y)
            case ThePoint(x, y, z):
                assert_type(x, int)
                assert_type(y, str)
                assert_type(z, float)
                return ("point", (x, y, z))
            case _:
                return ("none", None)

    assert match_point("x=1;") == ("x", 1)
    assert match_point("y=hello;") == ("y", "hello")
    assert match_point("x=1; y=hello; z=3.14") == ("point", (1, "hello", 3.14))
    assert match_point("unknown") == ("none", None)


def test_match_keyword_and_literal():
    def check(s: str) -> str:
        match MatchStr(s):
            case ThePoint(x=0, y="origin", z=z):
                assert_type(z, float)
                return f"origin z={z}"
            case ThePoint(x=x, y=y, z=0.0) if x > 0:
                assert_type(x, int)
                assert_type(y, str)
                return f"positive x={x}, y={y}"
            case _:
                return "other"

    assert check("x=0; y=origin; z=1.5") == "origin z=1.5"
    assert check("x=5; y=test; z=0.0") == "positive x=5, y=test"
    assert check("x=-5; y=test; z=0.0") == "other"


def test_match_conversions_and_types():
    @Conversion
    def percent(s: str) -> float:
        return float(s.rstrip("%")) / 100

    @FormatConversion
    def slice_str(s: str, spec: str) -> str:
        lo, hi = spec.split(",")
        return s[int(lo) : int(hi)]

    class Payload(TypedDict):
        id: int

    class ComplexMatcher(
        Matcher,
        parser=Parser(
            t"[{datetime.date:%Y-%m-%d}] {percent} {slice_str:1,4} {Payload}"
        ),
    ):
        dt: datetime.date
        rate: float
        code: str
        payload: Payload

    match MatchStr('[2025-05-01] 25% _abc_ {"id": 42}'):
        case ComplexMatcher(dt, rate, code, payload):
            assert_type(dt, datetime.date)
            assert_type(rate, float)
            assert_type(code, str)
            assert_type(payload, Payload)
            assert dt == datetime.date(2025, 5, 1)
            assert rate == 0.25
            assert code == "abc"
            assert payload == {"id": 42}
        case _:
            pytest.fail("Expected ComplexMatcher to match")


def test_matcher_instance_and_parse():
    p = ThePoint.parse("x=10; y=foo; z=2.5")
    assert_type(p, ThePoint)
    assert_type(p.x, int)
    assert_type(p.y, str)
    assert_type(p.z, float)
    assert p == ThePoint(10, "foo", 2.5)

    match p:
        case ThePoint(x, y, z):
            assert_type(x, int)
            assert_type(y, str)
            assert_type(z, float)
            assert (x, y, z) == (10, "foo", 2.5)
        case _:
            pytest.fail("Expected ThePoint instance to match")


def test_match_caches_parse_per_matcher():
    calls = 0

    @Conversion
    def tracked_int(s: str) -> int:
        nonlocal calls
        calls += 1
        return int(s)

    class ErrResp(Matcher, parser=Parser(t'code={tracked_int};error="{str}";')):
        code: int
        error: str

    def handle_response(raw: str) -> str:
        match MatchStr(raw):
            case ErrResp(400, error):
                return f"Error (400): {error}"
            case ErrResp(403, error):
                return f"Error (403): {error}"
            case ErrResp(500, error):
                return f"Error (500): {error}"
            case _:
                return "Unknown response"

    assert (
        handle_response('code=500;error="server error";') == "Error (500): server error"
    )
    assert calls == 1

    calls = 0
    assert handle_response("invalid") == "Unknown response"
    assert calls == 0


def test_match_interleaved_overlapping_fields():
    class TypeA(Matcher, parser=Parser(t"a={int};b={int}")):
        val: int
        other: int

    class TypeB(Matcher, parser=Parser(t"a={int};b={int}")):
        other: int
        val: int

    match MatchStr("a=1;b=2"):
        case TypeA(99, _):
            pytest.fail("Should not match val=99")
        case TypeB(99, _):
            pytest.fail("Should not match other=99")
        case TypeA(1, other):
            assert other == 2
        case _:
            pytest.fail("Expected TypeA(1, 2) to match")
