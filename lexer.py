from dataclasses import dataclass

@dataclass
class Token:
    type: str   # למשל 'NUMBER', 'OP'
    value: str  # למשל '34', '+'שכ

class Tokenizer:
    def __init__(self, text):
        self.text = text
        self.pos = 0   # איפה אנחנו בטקסט כרגע

    def tokenize(self):
        tokens = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]

            if ch == ' ':                 # חוק 1: רווח, מדלגים
                self.pos += 1
            elif ch in '+-*/=':           # חוק 3: אופרטור, טוקן בודד
                tokens.append(Token('OP', ch))
                self.pos += 1
            elif ch.isdigit():            # חוק 2: ספרה, קוראים מספר שלם
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
                raise SyntaxError(f"תו לא מוכר: {ch!r}")
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

