import pytest

from temparse import Parser, parse


def test_init():
    with pytest.raises(ValueError):
        Parser(t"some string without interpolations")


def test_match():
    with pytest.raises(ValueError):
        parse(t'"{str}"?', "teststr")


def test_type():
    with pytest.raises(TypeError):
        parse(t"x = {bytes}", "x = +31")
