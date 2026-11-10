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
| Parentheses in the parser | `parser.py` | 🚧 In progress |
| Variables and assignment | | ⏳ Planned |

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

Two node types are enough for trees of any depth:
- `Number(value)` – a leaf
- `BinOp(left, op, right)` – an operation whose children can be numbers or other operations

### 3. Evaluator
A recursive function that evaluates both children and then applies the operator.
It knows nothing about precedence; it simply walks the tree it is given.

### 4. Parser
A **recursive descent** parser with one function per precedence level:

```
parse_expression   handles + and -
    ↓
parse_term         handles * and /
    ↓
parse_factor       handles numbers
```

Each function keeps consuming tokens only while it sees its own operators,
which keeps multiplication deeper in the tree than addition.

```python
>>> tokens = Tokenizer("2 + 3 * 4").tokenize()
>>> tree = Parser(tokens).parse_expression()
>>> tree
BinOp(left=Number(value=2), op='+', right=BinOp(left=Number(value=3), op='*', right=Number(value=4)))
>>> evaluate(tree)
14
```

## Project structure

```
interpreter/
├── lexer.py        # Tokenizer: text → tokens
├── parser.py       # AST nodes, parser and evaluator
├── DECISIONS.md    # Design decisions and the reasoning behind them
├── README.md
└── .gitignore      # Keeps __pycache__ out of version control
```

## Running

Requires Python 3.14+.

```
python lexer.py
python parser.py
```

## Design decisions

Every non-obvious choice in this project, along with the alternatives considered,
is documented in [DECISIONS.md](DECISIONS.md).