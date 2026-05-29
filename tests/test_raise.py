import pytest

from temparse import parse


def test_match():
    with pytest.raises(ValueError):
        parse(t'"{str}"?', "teststr")


def test_type():
    with pytest.raises(TypeError):
        parse(t"x = {bytes}", "x = +31")
