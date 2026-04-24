# Python-to-C Compiler with IR Optimization

## Overview

This project is a compiler that translates basic Python into C code.

---

## Features

### IR-Based Compilation Pipeline
The compiler operates on a structured intermediate representation (IR) rather than raw source code. This allows for clearer transformation and optimization phases.

### Code Generation
The backend converts IR into valid C code, supporting:
- Functions
- Conditionals (`if/else`)
- For Loops
- Arithmetic and boolean expressions
- Function calls
- Dynamic list operations

---

## Optimizations

### 1. Constant Folding
Evaluates constant expressions at compile time to reduce runtime computation.

### 2. Strength Reduction
Replaces expensive operations with simpler equivalents (e.g., replacing multiplication by powers of two with bit shifts).

### 3. Dead Code Elimination
Removes unreachable code and unused intermediate variables by performing reachability analysis on the IR.

### 4. Converting to Capacity Based Lists
Uses lists that grow dynamically based on capacity, instead of reallocating on every append/remove.

### 5. List Boilerplate Removal
If lists are not used in a program, the compiler omits all list-related runtime code.

---

## Runtime System

The compiler includes a custom runtime implementation of Python-like lists in C.

### Features:
- Dynamic arrays with automatic resizing
- Support for integers, booleans, and nested lists
- Reference counting for memory management
- List comparison
- String conversion for printing

### Memory Management:
- Reference counting ensures safe sharing of nested lists
- Proper cleanup prevents memory leaks

---

## Usage

To run an example suite and compare results, do:
run.sh
The examples are in the example folder, while the output C is in the target_output folder.

To compile your own Python code, add a python file to the examples folder then do run.sh.

To view an example of our error detection system, do:
run.sh -error

To exclude some of our optimsations, you can use:
-noOpt1 -noOpt2 -noOpt3 -noOpt4 -noOpt5
The optimisation number matches the order of optimisations given above.
