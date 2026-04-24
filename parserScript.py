import sys
import os
from pythonParser import parser
from pythonLexer import lexer
from pythonAst import DictPrinter
import json

if __name__ == "__main__":
    os.makedirs('parsed_examples', exist_ok=True)

    for file_name in os.listdir('examples'):
        input_name = os.path.join('examples', file_name)
        print("Parsing " + input_name)
        output_name = os.path.join('parsed_examples', file_name)
        output_name = output_name.replace('.py', '.json')

        curr_input_file = open(input_name, "r")
        code = curr_input_file.read()

        lexer.lineno = 1
        lexer.input(code)

        ast = parser.parse(code, lexer=lexer)
        curr_output_file = open(output_name, "w")
        old_stdout = sys.stdout
        sys.stdout = curr_output_file
        
        print(json.dumps(DictPrinter().visit(ast), indent=2))

        sys.stdout = old_stdout
