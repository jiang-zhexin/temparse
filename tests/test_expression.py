from string.templatelib import Template

import temparse


def _test_expression(format: Template, expression: str):
    assert temparse.Parser(format)._expression == expression


def test_expressions():
    _test_expression(t"{str}", r"(.+?)")
    _test_expression(t"{str} {str}", r"(.+?)\ (.+?)")
