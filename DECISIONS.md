# Design Decisions

Every design choice in this project: what was chosen, what the alternatives were, and why.

---

## Project structure

### One file per stage
- **Decision:** `lexer.py` (text → tokens), `parser.py` (tokens → tree → result).
- **Alternative:** everything in a single file.
- **Why:** each file owns one stage, so each can be tested and fixed on its own. This mirrors how real interpreters are structured.

---

## Tokenizer (`lexer.py`)

### Tokens as a `@dataclass`
- **Decision:** a `Token` class with `type` and `value` fields.
- **Alternative:** a tuple such as `('NUMBER', '34')`.
- **Why:** `token.type` is more readable than `token[0]`, and `@dataclass` generates the constructor and a readable `repr` for free.

### A `while` loop with a position pointer
- **Decision:** walk the input with `while` and a `pos` index that we advance ourselves.
- **Alternative:** `for ch in text`.
- **Why:** tokens have variable length. A `for` loop always advances by exactly one character, with no way to skip ahead. Reading `345` or `total` means consuming several characters at once, and `pos` gives full control over how far to move.

### Separate helpers: `_read_number`, `_read_name`
- **Decision:** the main loop decides what to do; helper methods read multi-character tokens.
- **Alternative:** all logic inline in `tokenize`.
- **Why:** each function stays short and does one thing. The leading underscore marks them as internal, not meant to be called from outside.

### Fail loudly on unknown characters
- **Decision:** `raise SyntaxError` when a character matches no rule.
- **Alternative:** silently skip it.
- **Why:** silently skipping turns a typo into a confusing bug later on. An immediate error points straight at the problem.

### Bounds check before reading a character
- **Decision:** `self.pos < len(self.text) and (...)` in every inner loop, with parentheses around the second part.
- **Why:** without it, a token at the very end of the input causes an `IndexError`. Order matters because of short-circuit evaluation: Python skips the right side of `and` when the left side is `False`. Without the parentheses, `and` binds tighter than `or`, so the bounds check would not guard the whole condition.
- **How we found it:** a bug that only appeared when a variable name was the last token. Lesson: always test edge cases.

### Different rules for the first character of a name
- **Decision:** the first character must be `isalpha()` or `_`; the rest may be `isalnum()` or `_`.
- **Why:** this matches Python's own rules. If names could start with a digit, there would be no way to tell, on seeing `2`, whether it starts a number or a name.

### A separate token type for parentheses: `LPAREN`, `RPAREN`
- **Decision:** parentheses are not tagged as `OP`.
- **Why:** operators compute values; parentheses only group. The parser can then decide based on token type alone, without inspecting the value. Two types because `(` opens a group and `)` closes one, and the parser treats them differently.

---

## Syntax tree and evaluation (`parser.py`)

### Represent expressions as a tree (AST)
- **Decision:** convert the token list into a tree instead of computing directly from the list.
- **Why:** a flat list does not say what to compute first. In a tree, deeper nodes are evaluated first, so precedence is expressed by the tree's shape.

### Two node types: `Number` and `BinOp`
- **Decision:** a leaf holding one value, and an operation holding `left`, `op` and `right`.
- **Why:** `left` and `right` can themselves be `BinOp`, so two classes are enough for trees of any depth (a recursive structure).

### The evaluator knows nothing about precedence
- **Decision:** `evaluate` only computes children, then the parent, with no arithmetic rules of its own.
- **Why:** separation of concerns. The parser decides precedence when it builds the tree, so each part stays simple and rules live in one place.

### Recursive descent parser
- **Decision:** one function per precedence level: `parse_expression` (`+ -`), `parse_term` (`* /`), `parse_factor` (numbers).
- **Alternative we tried:** building the tree left to right. It produced `(2 + 3) * 4` instead of `2 + (3 * 4)`.
- **Why:** each function keeps going only while it sees its own operators, and asks the level below for its operands. `parse_term` finishes first and returns a whole multiplication group; `parse_expression` finishes last and wraps those groups, so `+` always ends up above `*`. Precedence comes from the structure of the code, not from explicit rules.
- **Associativity:** the loop `left = BinOp(left, op, right)` wraps everything built so far as the new left child, which gives left associativity: `10 - 2 - 3` is `(10 - 2) - 3 = 5`.

### A `current()` helper that returns `None` at the end
- **Decision:** every parsing function reads the current token through `current()`, which returns `None` when tokens run out.
- **Alternative:** index `self.tokens[self.pos]` directly in each function.
- **Why:** the bounds check lives in one place. This avoids the `IndexError` class of bugs we hit in the tokenizer, where every loop had to remember its own check.

### Convert number tokens with `int()` in the parser
- **Decision:** the tokenizer keeps values as strings; `parse_factor` converts them with `int(token.value)`.
- **Why:** the tokenizer's job is only to find tokens in the text. Giving them meaning belongs to the parser. Without the conversion, `'2' + '3'` would produce `'23'`.

---

## Tooling

### `if __name__ == "__main__":` around test code
- **Decision:** each module's test prints run only when the file is executed directly.
- **Why:** `parser.py` imports `lexer.py`, and Python runs a module's top-level code on import. Without the guard, every run of the parser would also print the lexer's test output.

### `.gitignore` with `__pycache__/`
- **Decision:** exclude Python's bytecode cache from version control.
- **Why:** it is generated automatically on every import, differs between machines and Python versions, and carries no information that is not already in the source.