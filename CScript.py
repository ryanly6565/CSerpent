import os
import sys
from CGen import TargetGenerator

if __name__ == "__main__":
    noOpt4 = False
    noOpt5 = False

    # Read command-line arguments
    for arg in sys.argv[1:]:
        if arg == "-noOpt4":
            noOpt4 = True
        elif arg == "-noOpt5":
            noOpt5 = True
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)

    os.makedirs('target_output', exist_ok=True)

    for file_name in os.listdir('ir_examples'):
        input_path = os.path.join('ir_examples', file_name)
        output_name = file_name.replace('.ir', '.c')
        output_path = os.path.join('target_output', output_name)

        print("Generating C for " + output_path)

        with open(input_path, "r") as f:
            lines = f.readlines()
        if file_name.__contains__('1') or file_name.__contains__('2'):
            pass
        tg = TargetGenerator()
        tg.generate(lines, noOpt4=noOpt4, noOpt5=noOpt5)

        curr_output_file = open(output_path, "w")
        old_stdout = sys.stdout
        sys.stdout = curr_output_file

        tg.print_code()

        sys.stdout = old_stdout
