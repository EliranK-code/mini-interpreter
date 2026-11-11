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

### Parentheses are handled in `parse_factor`
- **Decision:** when `parse_factor` sees `LPAREN`, it parses a full expression and returns it as a single factor.
- **Why:** from the outside, `(2 + 3)` behaves like one value. In `(2 + 3) * 4`, the multiplication only needs "one thing" on its left, and providing one thing is exactly the job of `parse_factor`. Handling parentheses at the lowest level gives them the highest precedence.

### Inside parentheses, call `parse_expression`, not `parse_term`
- **Decision:** the contents of parentheses are parsed with `parse_expression`, the top of the chain.
- **Alternative:** `parse_term`.
- **Why:** parentheses can contain any expression. `parse_term` only knows `*` and `/`, so on `(2 + 3)` it would stop at `+`. It works on `(2 * 3)`, which makes this a bug that only shows up on some inputs. Calling back up to `parse_expression` is the "recursive" in recursive descent, and it is what allows nesting like `((2 + 3) * 4)`.

### Parentheses do not appear in the tree
- **Decision:** `parse_factor` returns the inner tree as is, without wrapping it in a node.
- **Why:** parentheses only tell the parser how to shape the tree. Once the shape is built, `(2 + 3) * 4` is fully described by `+` sitting below `*`, and the evaluator needs nothing more.

### Require a closing `)` instead of skipping a token
- **Decision:** after the inner expression, check that the current token is `RPAREN`, otherwise raise `SyntaxError("Expected ')'")`.
- **Alternative:** blindly advance past whatever token is there.
- **Why:** fail loudly. Blindly skipping would accept `(2 + 3` and silently mis-parse the wrong-`parse_term` bug above. The `is None` check comes first because of short-circuit evaluation: `None` has no `.type`.

### A single `parse()` entry point that rejects leftover tokens
- **Decision:** callers use `parse()`, which runs `parse_expression()` and then checks that `current()` is `None`. Otherwise it raises `SyntaxError("Unexpected token: ...")`.
- **Alternative:** call `parse_expression()` directly.
- **Why:** `parse_expression()` stops as soon as it sees a token it does not handle and returns whatever it has built. On `"2 3"` it returns `2` and silently ignores the `3`; on `"2 + 3 4"` it returns `5`. A wrong answer that looks right is worse than an error, because nothing tells the user something is off. `parse()` also gives the parser one public entry point, so callers do not need to know about the internal `parse_*` levels.

### A `current()` helper that returns `None` at the end
- **Decision:** every parsing function reads the current token through `current()`, which returns `None` when tokens run out.
- **Alternative:** index `self.tokens[self.pos]` directly in each function.
- **Why:** the bounds check lives in one place. This avoids the `IndexError` class of bugs we hit in the tokenizer, where every loop had to remember its own check.

### Convert number tokens with `int()` in the parser
- **Decision:** the tokenizer keeps values as strings; `parse_factor` converts them with `int(token.value)`.
- **Why:** the tokenizer's job is only to find tokens in the text. Giving them meaning belongs to the parser. Without the conversion, `'2' + '3'` would produce `'23'`.

---

## Variables

### The environment is a dictionary
- **Decision:** variable values are stored in a `dict` that maps names to values.
- **Alternative:** a list of `(name, value)` pairs.
- **Why:** a list would need a linear search on every lookup. A dictionary is a hash table, so looking up a name takes O(1) on average.

### Pass the environment into `evaluate` as a parameter
- **Decision:** `evaluate(node, env)`; the caller creates `env` once and every recursive call passes it on.
- **Alternatives:** create the dictionary inside `evaluate`, or use a global variable.
- **Why:** a dictionary created inside `evaluate` would start empty on every call, so `x` from one line would be gone on the next. A global would work, but any code could change it unnoticed, and it would be impossible to run two independent evaluations. As a parameter, it is explicit who uses it, and each caller can have its own environment.

### Reading a variable: a `Name` node
- **Decision:** a new leaf type `Name(name)`, created by `parse_factor` for `NAME` tokens, and looked up by `evaluate`.
- **Why:** from the parser's point of view a variable is "one complete thing", just like a number, so it belongs in `parse_factor`. Its name stays a string; the value is only known at evaluation time. Everything else (precedence, parentheses) kept working without changes.

### A clear error for undefined variables
- **Decision:** check `node.name in env` and raise `NameError("Undefined variable: ...")`.
- **Alternative:** let `env[node.name]` raise `KeyError`.
- **Why:** `KeyError` describes how the interpreter is built inside, not what the user did wrong. The error should speak the user's language, as Python's own `name 'z' is not defined` does.

### Writing a variable: an `Assign` node with a plain string target
- **Decision:** `Assign(name: str, value: expression)`. `evaluate` computes `value`, stores it in `env[name]`, and returns it.
- **Alternative:** use a `Name` node as the left side.
- **Why:** the same `x` has opposite roles. On the right of `=` it is a source to read from; on the left it is a destination to write to and may not exist yet. A `Name` node would be evaluated, i.e. read, and fail with "Undefined variable" for the very variable being created.
- **Returning the value:** so the caller can show what was stored (`x = 2 + 3 → 5`). Python's own prompt prints nothing after an assignment; this is a deliberate difference.

### Detect assignment with one token of lookahead
- **Decision:** a `peek()` helper returns the token after the current one. `parse()` treats the line as an assignment only if it starts with a `NAME` token followed by a token whose value is `=`.
- **Why:** `x = 5` and `x * 2` both start with `x`; only the next token tells them apart. The check uses `.value` rather than `.type`, because `=` and `*` both have type `OP`. After recognising an assignment the parser advances by two tokens, consuming both the name and the `=`.

### Check node types before reaching the `BinOp` code
- **Decision:** in `evaluate`, the `Number`, `Name` and `Assign` branches all come before `left = evaluate(node.left, env)`.
- **Why:** that code assumes a `BinOp` with `left` and `right` fields. Any other node type that reached it would crash.

---

## REPL (`main.py`)

### The REPL lives in its own file
- **Decision:** `lexer.py` and `parser.py` hold the language; `main.py` holds the interactive prompt.
- **Why:** the language is a library, and the REPL is just one way to talk to it. Another interface (for example, running a whole file) could be added later without touching the language code.

### A `run(text, env)` helper
- **Decision:** one function that wraps the whole pipeline: tokenize, parse, evaluate.
- **Why:** callers do not need to know there are three stages. The REPL, and later the tests, call one function.

### The environment is created once, before the loop
- **Decision:** `env = {}` comes before `while True`.
- **Why:** if it were created inside the loop, every line would start with empty memory and `x` from the previous line would be gone.

### Catch only expected error types
- **Decision:** `except (SyntaxError, NameError, ZeroDivisionError)`.
- **Alternative:** `except Exception`, which catches everything.
- **Why:** these are the errors a user can cause with bad input. Catching everything would also hide real bugs in the interpreter. We saw this happen: an empty line caused an `AttributeError`, which revealed a missing check in `parse_factor`. Had it been caught, the bug would have looked like a user error.
- **Known limitation:** Python itself also raises `NameError` for undefined names in our own code. A leftover typo in the interpreter was once reported as a user error for this reason. A dedicated `InterpreterError` type would remove the overlap.

### Report the end of input clearly
- **Decision:** `parse_factor` raises `SyntaxError("Unexpected end of input")` when there is no token left.
- **Why:** inputs such as `2 +`, `(` or an empty line used to crash with `'NoneType' object has no attribute 'type'`, which describes the interpreter's internals rather than the user's mistake.

### Empty lines and leaving the REPL
- **Decision:** empty lines are skipped with `continue`; `exit`, Ctrl+C and end of input leave with `break`.
- **Why:** this matches Python's own prompt. The exit check comes before `run`, otherwise `exit` would be evaluated as an undefined variable. `input()` has its own `try`, separate from the one around `run`, because it handles a different kind of event: the user leaving, not the user making a mistake.

---

## Testing (`test_interpreter.py`)

### Automated tests with pytest
- **Decision:** tests are plain functions named `test_*` in a file named `test_*.py`, run with `pytest`.
- **Alternative:** checking printed output by eye after every change.
- **Why:** manual checks are slow and easy to skip. The bug with `and`/`or` in the tokenizer sat unnoticed for a day because no manual check had a name at the end of the input. The whole suite now runs in well under a second.

### Test through `run()`
- **Decision:** most tests call `run(text, env)` rather than the tokenizer, parser and evaluator separately.
- **Why:** it checks the full pipeline the user actually goes through, with one short line per case.

### Test that errors are raised, not only that results are correct
- **Decision:** `with pytest.raises(...)` checks that bad input produces the right error type.
- **Why:** failing correctly is part of the language's behaviour. A change that made `"2 3"` silently return `2` again would otherwise go unnoticed.

### A regression test for every bug found
- **Decision:** each bug fixed during development has its own test: a name at the end of the input, leftover tokens, a missing `)`, an undefined variable, division by zero, and empty input.
- **Why:** a bug that happened once can happen again. When the `and`/`or` bug was deliberately reintroduced, two tests failed immediately, including `test_undefined_variable`, which had not been written with that bug in mind but also ends with a name.

---

## Tooling

### `if __name__ == "__main__":` around test code
- **Decision:** each module's test prints run only when the file is executed directly.
- **Why:** `parser.py` imports `lexer.py`, and Python runs a module's top-level code on import. Without the guard, every run of the parser would also print the lexer's test output.

### `.gitignore` with `__pycache__/` and `.pytest_cache/`
- **Decision:** exclude Python's bytecode cache and pytest's cache from version control.
- **Why:** both are generated automatically, differ between machines, and carry no information that is not already in the source.