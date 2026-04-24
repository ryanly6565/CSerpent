import math

class IROptimizer:
    """
    Performs constant_folding, dead_code_elimination, and strength reduction
    """
    def __init__(self, ir_code):
        self.ir_code = ir_code

    def optimize(self, noOpt1, noOpt2, noOpt3):
        """
        Run all optimizations in sequence
        """
        code = self.ir_code

        # order
        if (not noOpt1):
            code = self.constant_folding(code)
        if (not noOpt2):
            code = self.strength_reduction(code)
        if (not noOpt3):
            code = self.dead_code_elimination(code, unused_vars=[])

        return code
    
    @staticmethod
    def constant_folding(ir_code):
        """
        Evaluate constant expressions at compile time.
        Example: _t1 := 2 + 3  becomes  _t1 := 5
        """
        optimized = []
        for line in ir_code:
            # Check if it's an assignment with constants
            if ':=' in line and not line.strip().startswith('if'):
                parts = line.split(':=')
                if len(parts) == 2:
                    dest = parts[0].strip()
                    expr = parts[1].strip()
                    
                    # Try to evaluate constant expressions
                    try:
                        # Check for simple binary ops with constants
                        for op in ['+', '-', '*', '/']:
                            if op in expr and not any(c.isalpha() and c != '_' for c in expr.replace('_t', '')):
                                # Try to evaluate
                                result = eval(expr)
                                line = f"    {dest} := {result}"
                                break
                    except:
                        pass
            optimized.append(line)
        return optimized
    
    @staticmethod
    def dead_code_elimination(ir_code, unused_vars):
        """
        Remove assignments to variables that are never used.
        Remove code that is never reached.
        """
        optimized_stage_one = []
        for line in ir_code:
            keep = True
            if ':=' in line and not line.strip().startswith('if'):
                parts = line.split(':=')
                dest = parts[0].strip()
                # If dest is a temp and not in used_vars, skip it
                if dest.startswith('_t') and dest in unused_vars:
                    keep = False
            if keep:
                optimized_stage_one.append(line)

        # remove lines that can't be reached
        optimized_stage_two = []
        line_explored = [False for line in optimized_stage_one]
        label_first_line = [False for line in optimized_stage_one]
        labels = {}
        for i, line in enumerate(optimized_stage_one):
            if line.endswith(':'):
                labels[line[:-1]] = i
        explore_pool = set()
        explore_pool.add((0, optimized_stage_one[0]))
        while(explore_pool):
            index, curr_line = explore_pool.pop()

            curr_line = curr_line.strip()
            line_explored[index] = True
            # handle jumps
            if curr_line.startswith("goto"):
                label = curr_line.split()[1]
                if not line_explored[labels[label]]:
                    explore_pool.add((labels[label], optimized_stage_one[labels[label]]))
            
            elif curr_line.startswith("FuncCall"):
                label = curr_line.strip().split()[1]
                if not line_explored[labels[label]]:
                    explore_pool.add((labels[label], optimized_stage_one[labels[label]]))
                if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                    explore_pool.add((index + 1, optimized_stage_one[index + 1]))
                    line_explored[labels[label]] = True

            elif " goto " in curr_line:
                label = curr_line.split(" goto ")[1]
                condition = curr_line.split("if",1)[1].split("goto",1)[0].strip()

                if condition.startswith("!(") and condition.endswith(")"):
                    condition = condition[2:-1]

                condition = condition.split()

                if len(condition) == 3:
                    left = condition[0]
                    op = condition[1]
                    right = condition[2]

                    if (left == "True" or left == "False") and (right == "True" or right == "False"):
                        left = True if left == "True" else False
                        right = True if right == "True" else False
                        result = False
                        if op == 'and':
                            result = left and right
                        elif op == 'or':
                            result = left or right

                        if not result:
                            if not line_explored[labels[label]]:
                                explore_pool.add((labels[label], optimized_stage_one[labels[label]]))
                        else:
                            if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                                explore_pool.add((index + 1, optimized_stage_one[index + 1]))
                                line_explored[labels[label]] = True
                                if labels[label] + 1 < len(optimized_stage_one):
                                    label_first_line[labels[label] + 1] = True # parsing if statements breaks if this is not here
                        
                    elif (str.isnumeric(left) or (len(left) > 1 and left[0] == "-" and str.isnumeric(left[1:]))) and \
                         (str.isnumeric(right) or (len(right) > 1 and right[0] == "-" and str.isnumeric(right[1:]))):
                        left = int(left)
                        right = int(right)
                        result = False
                        if op == '<':
                            result = left < right
                        elif op == '<=':
                            result = left <= right
                        elif op == '>':
                            result = left > right
                        elif op == '>=':
                            result = left >= right
                        elif op == '==':
                            result = left == right
                        elif op == '!=':
                            result = left != right

                        if not result:
                            if not line_explored[labels[label]]:
                                explore_pool.add((labels[label], optimized_stage_one[labels[label]]))
                        else:
                            if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                                explore_pool.add((index + 1, optimized_stage_one[index + 1]))
                                line_explored[labels[label]] = True
                                if labels[label] + 1 < len(optimized_stage_one):
                                    label_first_line[labels[label] + 1] = True # parsing if statements breaks if this is not here
                    
                    else:
                        label = curr_line.split()[-1]
                        if not line_explored[labels[label]]:
                            explore_pool.add((labels[label], optimized_stage_one[labels[label]]))
                        if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                            explore_pool.add((index + 1, optimized_stage_one[index + 1]))
                            line_explored[labels[label]] = True
                            if labels[label] + 1 < len(optimized_stage_one):
                                label_first_line[labels[label] + 1] = True # parsing if statements breaks if this is not here
                
                elif len(condition) == 2:
                    label = curr_line.split(" goto ")[1]
                    condition = condition[1]
                    if condition == "True" or str.isnumeric(condition) or (len(condition) > 1 and condition[0] == "-" and str.isnumeric(condition[1:])):
                        if not line_explored[labels[curr_line.split()[3]]]:
                            explore_pool.add((labels[curr_line.split()[3]], optimized_stage_one[labels[curr_line.split()[3]]]))
                    elif condition == "False" or condition == "0":
                        if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                            explore_pool.add((index + 1, optimized_stage_one[index + 1]))
                            line_explored[labels[label]] = True
                            if labels[label] + 1 < len(optimized_stage_one):
                                label_first_line[labels[label] + 1] = True # parsing if statements breaks if this is not here
                    
                    else:
                        label = curr_line.split()[-1]
                        if not line_explored[labels[label]]:
                            explore_pool.add((labels[label], optimized_stage_one[labels[label]]))
                        if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                            explore_pool.add((index + 1, optimized_stage_one[index + 1]))
                            line_explored[labels[label]] = True
                            if labels[label] + 1 < len(optimized_stage_one):
                                label_first_line[labels[label] + 1] = True # parsing if statements breaks if this is not here

                else:
                    label = curr_line.split(" goto ")[1]
                    condition = condition[0]
                    if condition == "False" or condition == "0":
                        if not line_explored[labels[curr_line.split()[3]]]:
                            explore_pool.add((labels[curr_line.split()[3]], optimized_stage_one[labels[curr_line.split()[3]]]))
                    elif condition == "True" or str.isnumeric(condition) or (len(condition) > 1 and condition[0] == "-" and str.isnumeric(condition[1:])):
                        if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                            explore_pool.add((index + 1, optimized_stage_one[index + 1]))
                            line_explored[labels[label]] = True
                            if labels[label] + 1 < len(optimized_stage_one):
                                label_first_line[labels[label] + 1] = True # parsing if statements breaks if this is not here
        
            else:
                # add next line if not end
                if (index + 1) < len(optimized_stage_one) and not line_explored[index + 1]:
                    explore_pool.add((index + 1, optimized_stage_one[index + 1]))

        for i, shouldAdd in enumerate(label_first_line):
            if shouldAdd:
                line_explored[i] = True
        for i, line in enumerate(optimized_stage_one):
            if line_explored[i]:
                optimized_stage_two.append(line)

        new_lines = []
        i = 0
        while i < len(optimized_stage_two):
            line = optimized_stage_two[i]
            info = line.strip().split()
            # check if line is an if
            if info and info[0] == "if":
                label = info[-1]
                # if next line is exactly the label, skip it
                if i + 1 < len(optimized_stage_two) and optimized_stage_two[i + 1].strip() == label + ":":
                    i += 1  # skip the label line
            new_lines.append(optimized_stage_two[i])
            i += 1
        return new_lines
    
    @staticmethod
    def strength_reduction(ir_code):
        """
        Replace expensive operations with cheaper equivalents.
        x * 2 -> x + x (or x << 1)
        x * 1 -> x
        x * 0 -> 0
        x + 0 -> x
        """
        optimized = []
        for line in ir_code:
            new_line = line
            
            if ':=' in line:
                # x * 2 -> x << 1 or x + x
                if '* ' in line:
                    new_line = line.replace('* 2', '<< 1')
                    parts = line.split(':=')
                    expr = parts[1].strip()
                    pieces = expr.split()
                    if int(pieces[2]) and int(pieces[2]) > 0 and int(pieces[2]) & (int(pieces[2]) - 1) == 0:
                        power_of_two = int(pieces[2])
                        new_line = line.replace('* ' + pieces[2], '<< ' + str(int(math.log2(power_of_two))))
                # x * 1 -> x
                elif '* 1' in line:
                    parts = line.split(':=')
                    expr = parts[1].strip()
                    var = expr.replace('* 1', '').strip()
                    new_line = f"    {parts[0].strip()} := {var}"
                # x * 0 -> 0
                if '*0' in line.replace(' ', ''):
                    parts = line.split(':=')      # split on assignment
                    new_line = f"    {parts[0].strip()} := 0"
                # x + 0 -> x
                elif '+ 0' in line:
                    parts = line.split(':=')
                    expr = parts[1].strip()
                    var = expr.replace('+ 0', '').strip()
                    new_line = f"    {parts[0].strip()} := {var}"
            
            optimized.append(new_line)
        return optimized