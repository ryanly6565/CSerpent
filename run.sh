#!/bin/bash
set -e

# Initialize options as false
noOpt1=false
noOpt2=false
noOpt3=false
noOpt4=false
noOpt5=false
runErrorTests=false

# Parse command-line arguments
for arg in "$@"; do
    case "$arg" in
        -noOpt1) noOpt1=true ;;
        -noOpt2) noOpt2=true ;;
        -noOpt3) noOpt3=true ;;
        -noOpt4) noOpt4=true ;;
        -noOpt5) noOpt5=true ;;
        -error) runErrorTests=true ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# If -error flag is set, run error tests and exit
if [ "$runErrorTests" = true ]; then
    echo "Running error test suite..."
    set +e

    declare -A examples
    examples["other_examples/bad_assign.py"]="Assignment error example"
    examples["other_examples/type_error_combining_types.py"]="Type error: combining incompatible types"
    examples["other_examples/type_error_changing_type.py"]="Type error: changing variable type"
    examples["other_examples/make_string.py"]="Error in string construction"
    examples["other_examples/missing_if_colon.py"]="Syntax error: missing colon in if statement"

    for file in "${!examples[@]}"; do
        echo "----------------------------------------"
        echo "Running $file"
        echo "Description: ${examples[$file]}"
        python3 test_error_script.py "$file"
        echo
    done

    exit 0
fi

echo "Options set:"
echo "noOpt1=$noOpt1"
echo "noOpt2=$noOpt2"
echo "noOpt3=$noOpt3"
echo "noOpt4=$noOpt4"
echo "noOpt5=$noOpt5"

# Run parser
python3 parserScript.py "$@"

# IR options
ir_opts=()
[ "$noOpt1" = true ] && ir_opts+=("-noOpt1")
[ "$noOpt2" = true ] && ir_opts+=("-noOpt2")
[ "$noOpt3" = true ] && ir_opts+=("-noOpt3")

python3 irScript.py "${ir_opts[@]}"

# C options
c_opts=()
[ "$noOpt4" = true ] && c_opts+=("-noOpt4")
[ "$noOpt5" = true ] && c_opts+=("-noOpt5")

python3 CScript.py "${c_opts[@]}"

# Build
make

# Run test comparisons
for pyfile in "examples"/*.py; do
    name=$(basename "$pyfile" .py)

    echo "Running Python: $pyfile"
    python3 "$pyfile" > "target_results/${name}.py.out"

    echo "Running C: $name"
    "target_output/$name" > "target_results/${name}.c.out"

    echo "Diff Results:"
    if diff "target_results/${name}.py.out" "target_results/${name}.c.out" > "target_results/${name}.diff"; then
        echo "Results match!"
        rm "target_results/${name}.diff"
    else
        diff "target_results/${name}.py.out" "target_results/${name}.c.out"
        rm "target_results/${name}.diff"
    fi
done