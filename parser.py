from dataclasses import dataclass
from lexer import Tokenizer

@dataclass
class Number:
    value: int


@dataclass
class BinOp:
    left: Number | BinOp
    op: str
    right: Number | BinOp


def evaluate(node):
    if isinstance(node, Number):
        return node.value

    left = evaluate(node.left)
    right = evaluate(node.right)

    if node.op == '+':
        return left + right
    if node.op == '*':
        return left * right
    if node.op == '-':
        return left - right
    if node.op == '/':
        return left / right
    
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def parse_factor(self):
        token = self.current()        # הטוקן הנוכחי
        self.pos += 1     # בכמה מתקדמים?
        return Number(int(token.value))   # מה שמים בפנים?


    def parse_term(self):
        left = self.parse_factor()

        while self.current() is not None and self.current().value in ('*', '/'):
            op = self.current().value
            self.pos += 1
            right = self.parse_factor()
            left = BinOp(left, op, right)

        return left

    def parse_expression(self):
        left = self.parse_term()

        while self.current() is not None and self.current().value in ('+', '-'):
            op = self.current().value
            self.pos += 1
            right = self.parse_term()
            left = BinOp(left, op, right)

        return left

    
for text in ["2 + 3 * 4", "2 * 3 + 4", "10 - 2 - 3", "8 / 2 * 4"]:
    tree = Parser(Tokenizer(text).tokenize()).parse_expression()
    print(text, "=", evaluate(tree))