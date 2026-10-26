import pytest

from temparse import Matcher, Parser, parse


def test_init():
    with pytest.raises(ValueError):
        Parser(t"some string without interpolations")


def test_match():
    with pytest.raises(ValueError):
        parse(t'"{str}"?', "teststr")


def test_type():
    with pytest.raises(TypeError):
        parse(t"x = {bytes}", "x = +31")


def test_matcher():
    class TheX(Matcher, parser=Parser(t"x={int}")):
        x: int

    with pytest.raises(ValueError):
        TheX.parse("invalid")

    with pytest.raises(ValueError):

        class _InvalidMatcher(Matcher, parser=Parser(t"x={int}, y={int}")):
            x: int
