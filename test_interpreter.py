import pytest
from parser import run


def test_number():
    assert run("42", {}) == 42


def test_addition():
    assert run("2 + 3", {}) == 5

def test_precedence():
    assert run("2 + 3 * 4", {}) == 14


def test_parentheses():
    assert run("(2 + 3) * 4", {}) == 20


def test_left_associativity():
    assert run("10 - 2 - 3", {}) == 5


def test_variables():
    env = {}
    run("x = 5", env)
    assert run("x * 2", env) == 10


def test_incomplete_expression():
    with pytest.raises(SyntaxError):
        run("2 +", {})

def test_name_at_end():
    env = {}
    run("y = 3", env)
    assert run("2 + y", env) == 5

def test_leftover_tokens():
    with pytest.raises(SyntaxError):
        run("2 3", {})

def test_missing_paren():
    with pytest.raises(SyntaxError):
        run("(2 + 3", {})

def test_undefined_variable():
    with pytest.raises(NameError):
        run("z", {})

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        run("1 / 0", {})

def test_empty_input():
    with pytest.raises(SyntaxError):
        run("", {})