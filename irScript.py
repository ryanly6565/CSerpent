import os
import sys
import ast as pyast
import re
from pythonIR import IRGenerator
from IROptimizer import IROptimizer

if __name__ == "__main__":
    noOpt1 = False
    noOpt2 = False
    noOpt3 = False

    # Read command-line arguments
    for arg in sys.argv[1:]:
        if arg == "-noOpt1":
            noOpt1 = True
        elif arg == "-noOpt2":
            noOpt2 = True
        elif arg == "-noOpt3":
            noOpt3 = True
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)

    os.makedirs('ir_examples', exist_ok=True)

    for file_name in os.listdir('parsed_examples'):
        input_path = os.path.join('parsed_examples', file_name)
        output_name = file_name.replace('.json', '.ir')
        output_path = os.path.join('ir_examples', output_name)

        with open(input_path, "r") as f:
            content = f.read()
            content = re.sub(r'\bnull\b', 'None', content)
            content = re.sub(r'\btrue\b', 'True', content)
            content = re.sub(r'\bfalse\b', 'False', content)
            ast_dict = pyast.literal_eval(content)

        print("Generating Optimized IR for: " + output_path)

        ir_gen = IRGenerator()
        ir_gen.generate(ast_dict)
        optimized_ir = ir_gen.ir_code
        optimizer = IROptimizer(ir_gen.ir_code)
        optimized_ir = optimizer.optimize(noOpt1, noOpt2, noOpt3)

        with open(output_path, "w") as f_out:
            for line in optimized_ir:
                f_out.write(line + "\n")