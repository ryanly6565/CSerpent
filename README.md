# CSerpent

**A Python-to-C compiler using a three-address intermediate representation, optional optimization flags, and a custom dynamic-list runtime.**

CSerpent is a compiler meant for translating a subset of Python into C, it also compiles the generated C code with GCC. CSerpent was built as a compiler course project, it covers the pipeline of: lexical analysis, parsing, AST construction, IR generation, type inference, optimization, and code generation.

## Features

- Supported Python includes:
    - Arithmetic operations, comparisons, boolean expressions, and variable assignments.
    - `if`, `elif`, and `else` statements.
    - `for` loops over `range()`.
    - Functions, CSerpent will infer parameter and return types.
    - Lists with potentially varying element types (i.e. heterogenous lists are supported, as are nested lists).
    - List operations like: `append()`, `remove()`, `pop(index)`, and `len()`.
- Independently configurable optimizations.
- An example suite comparing Python output with the CSerpent compiled C version.
- Error examples for malformed syntax.

## Quick start

Use Linux or WSL with Python 3, GCC, and Make installed. The parser and lexer both use [PLY](https://www.dabeaz.com/ply/).

```bash
git clone https://github.com/ryanly6565/CSerpent.git
cd CSerpent

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install ply

bash run.sh
```

All commands should be ran from the project root. The script will parse the pre-made examples, generate optimized IR and C, compile the C programs, and finally compare their output against the original Python code. A successful match is reported as `Results match!`.

## Compile your own program

The current pipeline will process every single file in `examples/`. To compiled a custom file, add a `.py` file to the examples folder, then run `bash run.sh`. For example, we could create the file `examples/list_demo.py`:

```python
items = [1, True, [2, 3]]
items.append(4)
print(items)
last = items.pop(3)
print(last)
print(len(items))
```

Once we run the bash, the following files will be created for `list_demo.py`:

| Artifact | Path |
| --- | --- |
| AST | `parsed_examples/list_demo.json` |
| Optimized IR | `ir_examples/list_demo.ir` |
| Generated C | `target_output/list_demo.c` |
| Compiled executable | `target_output/list_demo` |
| Python output | `target_results/list_demo.py.out` |
| C output | `target_results/list_demo.c.out` |

## Compilation pipeline

1. **Lexing and parsing:** We use PLY to tokenize the source code and build an abstract syntax tree using our custom grammar.
2. **IR generation:** The AST is converted into three-address code. To do this, expressions may be rewritten to use temporary variables, and control flow changes like function calls and loops are replaced with labels and jumps.
3. **IR optimization:** Various optimization techniques like constant folding, strength reduction, and dead code elimination are used to optimize the code.
4. **Type inference and C generation:** An IR interpreter determines typing and checks for type mismatching. The backend reconstructs code as C, emitting types for the C declarations, and including CSerpent's Python-style list code when needed.
5. **Compilation and verification:** GCC will output an executable C version. Both versions are ran and their standard outputs are compared against each other with `diff`.

To elaborate on point 2, an expression such as `x = a + b * c` is lowered into simpler operations:

```text
_t1 := b * c
_t2 := a + _t1
x := _t2
```

Type inference is done by executing IR during code generation, analysis is not static.

## Supported language subset

| Category | Supported forms |
| --- | --- |
| Values | Integers, `True`, `False`, and lists; `None` for return expressions |
| Assignment | `name = expression` |
| Arithmetic | `+`, `-`, `*`, `//`, unary `-`, and parentheses |
| Comparisons | `<`, `>`, `<=`, `>=`, `==`, `!=` for scalar expressions |
| Boolean logic | `and`, `or`, `not` |
| Conditionals | `if (condition):`, `elif (condition):`, `else:` |
| Loops | `for name in range(stop):`, `range(start, stop)`, or `range(start, stop, step)` with positive steps |
| Functions | Definitions with at least one parameter, only positional calls (func(a=1, b=2)), and a final return statement |
| Lists | Literals, nested lists, `append(value)`, `remove(value)`, `pop(index)`, `len(list)` |
| Output | `print(expression)` with one argument, including list printing |
| Comments | `#` comments |

Variables and function parameters must have a consistent type. Even though `a = 1` followed by `a = []` is valid Python, it would be hard to naturally translate this to C, and thus is rejected. Arithmetic between boolean and integers is rejected.

### Current limitations

- CSerpent only implements a subset of Python, it cannot handle the entire language or libraries.
- Conditions in `if` and `elif` statements require parentheses around them.
- Zero-argument function definitions are not part of the grammar.
- The Python top-level statements become the main body of the C, thus a Python main function like `def main()` is not supported
- `pop()` requires an index argument.
- Descending ranges in for loops are not implemented.
- Strings, floats, arbitrary-precision integers, imports, classes, and `while` loops are outside the supported subset of Python.
- Custom Python files submitted to CSerpent must match the required formatting exactly.

## Optimizations

CSerpent comes with five optional optimizations, all of which are enabled by default when using `run.sh`.

| # | Optimization | Purpose | Disable flag |
| --- | --- | --- | --- |
| 1 | Constant folding | Evaluate constant arithmetic expressions directly in the IR. | `-noOpt1` |
| 2 | Strength reduction | Simplify operations such as multiplication by powers of two, multiplication by zero or one, and addition of zero. | `-noOpt2` |
| 3 | Dead code elimination | Remove unused assignments and unreachable instructions. | `-noOpt3` |
| 4 | Capacity-based lists | Grow the list buffer size geometrically instead of having to reallocate a new C array on every change. | `-noOpt4` |
| 5 | List runtime removal | Omit list runtime definitions when the IR contains no list initialization. | `-noOpt5` |

Flags can be combined:

```bash
# Disable constant folding and strength reduction
bash run.sh -noOpt1 -noOpt2

# Disable all optimizations
bash run.sh -noOpt1 -noOpt2 -noOpt3 -noOpt4 -noOpt5
```

## List runtime

Any lists that exist in the original Python code are replicated in C using a custom runtime library. Each element in this list library will store its type and value, this allows integers, booleans, and nested lists to share an array, similar to a Python style list.

The list structure itself tracks list size, list capacity, a pointer to the data buffer, and reference count for each list element. List buffers starts with capacity eight and doubles in size when necessary. Reference counting helpers are used to manage shared and nested lists. Equality helpers are used for runtime operations like removing list values.

The baseline runtime is in `python_list_struct.c`; the capacity-based version is in `python_list_struct_optimized.c`.

## Verification

```bash
# Compile examples and compare Python/C output
bash run.sh

# Exercise syntax and type error examples
bash run.sh -error
```

The above error runner prints diagnostics for the malformed programs contained in `other_examples/`.

| Examples | Coverage |
| --- | --- |
| 1–3 | Assignments, boolean expressions, conditionals, and basic functions |
| 4–7 | List operations, loops, more complex functions, and lists as arguments |
| 8 | Repeated list appends for allocation behavior |
| 9 | Unreachable code elimination |
| 10 | Constant folding and strength reduction |

### Run individual stages

```bash
python3 parserScript.py  # examples/ -> parsed_examples/
python3 irScript.py      # parsed_examples/ -> ir_examples/
python3 CScript.py       # ir_examples/ -> target_output/*.c
make                    # generated C -> executables
```

`irScript.py` accepts `-noOpt1`, `-noOpt2`, and `-noOpt3`. `CScript.py` accepts `-noOpt4` and `-noOpt5`.

## Project structure

| File or directory | Role |
| --- | --- |
| `pythonLexer.py`, `pythonParser.py` | PLY lexer and grammar |
| `pythonAst.py` | AST nodes and serialization visitors |
| `pythonIR.py` | Three-address IR generation |
| `IROptimizer.py` | IR optimization passes |
| `ir_interpreter.py` | IR execution, type inference, and type checks |
| `CGen.py` | C code generation |
| `python_list_struct*.c` | Baseline and optimized list runtimes |
| `parserScript.py`, `irScript.py`, `CScript.py` | Pipeline stage runners |
| `run.sh`, `Makefile` | End-to-end execution and C compilation |
| `examples/`, `other_examples/` | Supported programs and error demonstrations |
| `parsed_examples/`, `ir_examples/`, `target_output/` | Intermediate and generated artifacts |
| `target_results/` | Captured Python and C output |

## Acknowledgments

Parts of the lexer, parser, and IR design were adapted from course tutorial material, as noted in the source code. The project extends that foundation with C generation, heterogeneous lists, type checks, and optimization passes.