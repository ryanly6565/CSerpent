#used ai to help make this
import os
import sys
from pythonParser import parser
from pythonLexer import lexer
from pythonAst import DictPrinter
from pythonIR import IRGenerator
from CGen import TargetGenerator

if len(sys.argv) < 2:
    print("Usage: python generate_c.py <input_file.py>")
    sys.exit(1)

input_file = sys.argv[1]
output_dir = 'other_examples'
base_name = os.path.splitext(os.path.basename(input_file))[0]
c_output_path = os.path.join(output_dir, base_name + '.c')

with open(input_file, 'r') as f:
    code = f.read()

lexer.lineno = 1
lexer.input(code)
ast_tree = parser.parse(code, lexer=lexer)
ast_dict = DictPrinter().visit(ast_tree)

ir_gen = IRGenerator()
ir_gen.generate(ast_dict)

tg = TargetGenerator()
tg.generate(ir_gen.ir_code)

with open(c_output_path, 'w') as f:
    if hasattr(tg, 'ir_code'):
        for line in tg.ir_code:
            f.write(line + '\n')
    if hasattr(tg, 'print_code'):
        old_stdout = sys.stdout
        sys.stdout = f
        tg.print_code()
        sys.stdout = old_stdout

print(f"Generated C file: {c_output_path}")
