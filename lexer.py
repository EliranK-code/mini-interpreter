from dataclasses import dataclass

@dataclass
class Token:
    type: str   
    value: str  

class Tokenizer:
    def __init__(self, text):
        self.text = text
        self.pos = 0   

    def tokenize(self):
        tokens = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]

            if ch == ' ':                
                self.pos += 1
            elif ch in '+-*/=':          
                tokens.append(Token('OP', ch))
                self.pos += 1
            elif ch.isdigit():           
                tokens.append(self.read_number())
            elif ch.isalpha() or ch == '_':
                tokens.append(self.read_name())
            elif ch == '(':
                tokens.append(Token('LPAREN', ch))
                self.pos += 1
            elif ch == ')':
                tokens.append(Token('RPAREN', ch))
                self.pos += 1
            else:
                raise SyntaxError(f"Unknown {ch!r}")
        return tokens

    def read_number(self):
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        return Token('NUMBER', self.text[start:self.pos])

    def read_name(self):
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return Token('NAME', self.text[start:self.pos])

    
if __name__ == "__main__":
    print(Tokenizer("(x2 + 34) * y").tokenize())

