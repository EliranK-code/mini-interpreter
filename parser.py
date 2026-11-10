from dataclasses import dataclass
from lexer import Tokenizer

@dataclass
class Number:
    value: int

@dataclass
class Name:
    name: str
    

@dataclass
class BinOp:
    left: Number | BinOp
    op: str
    right: Number | BinOp

@dataclass
class Assign:
    name: str                          
    value: Number | Name | BinOp     

def evaluate(node, env):
    if isinstance(node, Number):
        return node.value
    
    if isinstance(node, Name):
        if node.name not in env:
            raise NameError(f"Undefined variable: {node.name!r}")
        return env[node.name]
    
    if isinstance(node, Name):
        return env[node.name]

    if isinstance(node, Assign):
        result = evaluate(node.value, env)
        env[node.name] = result
        return result
    
    
    left = evaluate(node.left, env)
    right = evaluate(node.right, env)

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
    
    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None
    
    def parse_factor(self):
        token = self.current()

        if token.type == 'LPAREN':
            self.pos += 1                        
            inner = self.parse_expression()  
            if self.current() is None or self.current().type != 'RPAREN':
                raise SyntaxError("Expected ')'")            
            self.pos += 1                       
            return inner
        if token.type == 'NAME':
            self.pos += 1
            return Name(token.value)

        self.pos += 1
        return Number(int(token.value)) 

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

    def parse(self):
        if (self.current() is not None and self.current().type == 'NAME'
                and self.peek() is not None and self.peek().value == '='):
            name = self.current().value
            self.pos += 2
            value = self.parse_expression()
            tree = Assign(name, value)
        else:
            tree = self.parse_expression()

        if self.current() is not None:
            raise SyntaxError(f"Unexpected token: {self.current().value!r}")
        return tree
    
if __name__ == "__main__":
    env = {}
    for line in ["x = 2 + 3", "y = x * 2", "x + y", "z = (x + y) * 2", "z - 1"]:
        tree = Parser(Tokenizer(line).tokenize()).parse()
        print(line, "→", evaluate(tree, env))
    print(env)