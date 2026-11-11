# Mini Interpreter

A small interpreter for arithmetic expressions and variables, written from scratch in Python.
Built as a learning project to understand how programming languages work under the hood:
turning raw text into tokens, tokens into a syntax tree, and a syntax tree into a result.

```
"2 + 3 * 4"  →  Tokenizer  →  Parser  →  AST  →  Evaluator  →  14
```

## Status

| Stage | File | Status |
|---|---|---|
| Tokenizer (text → tokens) | `lexer.py` | ✅ Done |
| AST nodes + Evaluator (tree → result) | `parser.py` | ✅ Done |
| Parser (tokens → tree) for `+ - * /` | `parser.py` | ✅ Done |
| Parentheses in the parser | `parser.py` | ✅ Done |
| Variables and assignment | `parser.py` | ✅ Done |
| Interactive prompt (REPL) | `main.py` | ✅ Done |
| Automated tests | `test_interpreter.py` | ✅ Done |

## How it works

### 1. Tokenizer
Reads the input one character at a time and groups characters into **tokens**:
numbers, names, operators and parentheses. Whitespace is skipped.

```python
>>> Tokenizer("(x2 + 34) * y").tokenize()
[Token(type='LPAREN', value='('), Token(type='NAME', value='x2'),
 Token(type='OP', value='+'), Token(type='NUMBER', value='34'),
 Token(type='RPAREN', value=')'), Token(type='OP', value='*'),
 Token(type='NAME', value='y')]
```

### 2. Abstract Syntax Tree (AST)
Expressions are represented as a tree. Deeper nodes are evaluated first,
so operator precedence is encoded entirely in the shape of the tree:

```
2 + 3 * 4            (2 + 3) * 4

    +                    *
   / \                  / \
  2   *                +   4
     / \              / \
    3   4            2   3

  = 14                 = 20
```

Four node types cover the whole language:
- `Number(value)` – a numeric leaf
- `Name(name)` – a variable being read
- `BinOp(left, op, right)` – an operation whose children can be any expression
- `Assign(name, value)` – stores the result of an expression under a name

### 3. Evaluator
A recursive function that evaluates both children and then applies the operator.
It knows nothing about precedence; it simply walks the tree it is given.

Variables live in an **environment**: a dictionary passed into `evaluate`,
so values survive from one line to the next.

```python
>>> env = {}
>>> for line in ["x = 2 + 3", "y = x * 2", "(x + y) * 2"]:
...     print(line, "→", evaluate(Parser(Tokenizer(line).tokenize()).parse(), env))
x = 2 + 3 → 5
y = x * 2 → 10
(x + y) * 2 → 30
>>> env
{'x': 5, 'y': 10}
```

### 4. Parser
A **recursive descent** parser with one function per precedence level:

```
parse_expression   handles + and -
    ↓
parse_term         handles * and /
    ↓
parse_factor       handles numbers, names and ( ... )
    ↺ calls parse_expression again inside parentheses
```

`parse()` is the entry point. It looks one token ahead to tell an assignment
(`x = ...`) from an expression that merely starts with a name (`x * 2`),
and rejects any tokens left over at the end.

Each function keeps consuming tokens only while it sees its own operators,
which keeps multiplication deeper in the tree than addition.

```python
>>> tokens = Tokenizer("2 + 3 * 4").tokenize()
>>> tree = Parser(tokens).parse()
>>> tree
BinOp(left=Number(value=2), op='+', right=BinOp(left=Number(value=3), op='*', right=Number(value=4)))
>>> evaluate(tree, {})
14

>>> Parser(Tokenizer("2 + 3 4").tokenize()).parse()
SyntaxError: Unexpected token: '4'
```

Invalid input is rejected with a clear error instead of being silently ignored.

### 5. REPL
An interactive prompt that reads a line, runs it, prints the result and loops.
Variables persist between lines, and errors are reported without stopping the session.

```
>>> x = 5
5
>>> y = x * 2
10
>>> z
Error: Undefined variable: 'z'
>>> 1 / 0
Error: division by zero
>>> 2 +
Error: Unexpected end of input
>>> x + y
15
>>> exit
```

## Project structure

```
interpreter/
├── main.py              # REPL: the interactive prompt (entry point)
├── lexer.py             # Tokenizer: text → tokens
├── parser.py            # AST nodes, parser, evaluator and run()
├── test_interpreter.py  # Automated tests (pytest)
├── DECISIONS.md         # Design decisions and the reasoning behind them
├── README.md
└── .gitignore           # Keeps generated caches out of version control
```

## Running

Requires Python 3.14+.

```
python main.py
```

Type `exit` or press Ctrl+C to quit.

## Testing

```
pip install pytest
pytest
```

The suite covers arithmetic, precedence, associativity, parentheses and variables,
plus every bug found during development, so that none of them can come back unnoticed.

## Design decisions

Every non-obvious choice in this project, along with the alternatives considered,
is documented in [DECISIONS.md](DECISIONS.md).