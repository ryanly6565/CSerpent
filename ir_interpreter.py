from collections import deque
import copy
import sys

class IR_Interpret:
    def __init__(self, ir_lines):
        self.ir_lines = [l.strip() for l in ir_lines if l.strip()]
        self.labels = self.build_label_map()
        self.ret = [None, None, None]
        self.param_index = 0
        self.types = {}
        self.values = {}
        self.list_types = {}
        self.variable_types_shadow_stack = []
        self.variable_values_shadow_stack = []
        self.variable_lists_shadow_stack = []
        self.param_stack = []
        self.param_name_stack = []
        self.call_stack = []
        self.pending_params = []

        self.func_types = {}
        self.funcs = []
    
    def infer_type(self, val):
        """Infer C type from a value string"""
        if val in ('True', 'False'):
            return 'bool', True if val == 'True' else False
        if val.lstrip('-').isdigit():
            if str(val).startswith('-'):
                return 'int', -1 * int(val.lstrip('-'))
            return 'int', int(val.lstrip('-'))
        # look up known variable type
        if val == '[]':
            return 'python_list *', []
        
        return self.types.get(val), self.values.get(val)
    


    def build_label_map(self):
        labels = {}
        for i, line in enumerate(self.ir_lines):
            if line.endswith(':'):
                labels[line[:-1]] = i
        return labels

    def run(self):
        pc = 0

        while pc < len(self.ir_lines):
            line = self.ir_lines[pc]
            info = line.split()

            if line.endswith(':') or line[0] == 'Print':
                pc += 1
                continue

            if ':=' in line:
                name, expr = [x.strip() for x in line.split(' := ')]

                old_type = self.types[name] if name in self.types else None

                if (expr == 'ret'):
                    self.types[name] = self.ret[0]
                    self.values[name] = self.ret[1]
                    self.list_types[name] = self.ret[2]
                    self.ret = [None, None, None]

                # if its return value add it to ret instead of variable environment
                elif name == 'ret':
                    if expr.isdigit():
                        self.ret[1] = int(expr)
                        self.ret[0] = "int"

                    elif expr in ("True", "False"):
                        self.ret[1] = expr == "True"
                        self.ret[0] = "bool"
                    
                    elif len(expr.split()) == 2:
                        op, val = expr.split()
                        if op == 'not':
                            self.ret[1] = not self.infer_type(val)[1]
                            self.ret[0] = "bool"

                        elif op == 'Length':
                            if self.infer_type(val)[0] != "python_list *":
                                sys.exit(f"Error at line {pc+1} of IR: getting length of non-list. Line: {line}")
                            self.ret[1] = len(self.values[val])
                            self.ret[0] = 'int'         

                    elif len(expr.split()) == 3:
                        l, op, r = expr.split()

                        if l == 'Pop':
                            lst_type, lst = self.infer_type(op)
                            if lst_type != "python_list *":
                                sys.exit(f"Error at line {pc+1} of IR: cannot pop from non-list. Line: {line}")
                            self.ret[1] = self.values[l].pop(int(r))
                            self.ret[0] = self.list_types[l].pop(int(r))

                        else:
                            lv = self.infer_type(l)[1]
                            rv = self.infer_type(r)[1]

                            if op == '+':
                                self.ret[1] = lv + rv
                                self.ret[0] = "int"
                            elif op == '-':
                                self.ret[1] = lv - rv
                                self.ret[0] = "int"
                            elif op == '*':
                                self.ret[1] = lv * rv
                                self.ret[0] = "int"
                            elif op == '/':
                                self.ret[1] = lv // rv
                                self.ret[0] = "int"
                            elif op == '<':
                                self.ret[1] = lv < rv
                                self.ret[0] = "bool"
                            elif op == '<=':
                                self.ret[1] = lv <= rv
                                self.ret[0] = "bool"
                            elif op == '>':
                                self.ret[1] = lv > rv
                                self.ret[0] = "bool"
                            elif op == '>=':
                                self.ret[1] = lv >= rv
                                self.ret[0] = "bool"
                            elif op == '==':
                                self.ret[1] = lv == rv
                                self.ret[0] = "bool"
                            elif op == '!=':
                                self.ret[1] = lv != rv
                                self.ret[0] = "bool"
                            elif op == 'and':
                                self.ret[1] = lv and rv
                                self.ret[0] = "bool"
                            elif op == 'or':
                                self.ret[1] = lv or rv
                                self.ret[0] = "bool"
                    
                    elif expr == "[]":
                        self.ret[1] = []
                        self.ret[0] = "python_list *"
                        self.ret[2] = []

                    else:
                        self.ret[0], self.ret[1] = self.infer_type(expr)
                        # if this is a varibale list, also copy the list types
                        if self.ret[0] == 'python_list *':
                            self.ret[1] = copy.deepcopy(self.ret[1])
                            self.ret[2] = copy.deepcopy(self.list_types[expr])

                elif expr.isdigit():
                    self.values[name] = int(expr)
                    self.types[name] = "int"

                elif expr in ("True", "False"):
                    self.values[name] = expr == "True"
                    self.types[name] = "bool"

                elif len(expr.split()) == 2:
                    op, val = expr.split()
                    if op == 'not':
                        self.values[name] = not self.infer_type(val)[1]
                        self.types[name] = "bool"

                    elif op == 'Length':
                        self.values[name] = len(self.values[val])
                        self.types[name] = 'int'

                elif len(expr.split()) == 3:
                    l, op, r = expr.split()
                                            
                    if l == 'Pop':
                        lst_type, lst = self.infer_type(op)
                        if lst_type != "python_list *":
                            sys.exit(f"Error at line {pc+1} of IR: cannot pop from non-list. Line: {line}")
                        if self.infer_type(r)[0] != 'int':
                            sys.exit(f"Error at line {pc+1} of IR: pop index is non-int. Line: {line}")
                        self.values[name] = self.values[op].pop(int(r))
                        self.types[name] = self.list_types[op].pop(int(r))


                    else:
                        lv_type, lv = self.infer_type(l)
                        rv_type, rv = self.infer_type(r)

                        if lv_type != rv_type:
                            print(lv_type)
                            print(rv_type)
                            sys.exit(f"Error at line {pc+1} of IR: trying to combine 2 different types: {line}")

                        if op == '+':
                            self.values[name] = lv + rv
                            self.types[name] = "int"
                        elif op == '-':
                            self.values[name] = lv - rv
                            self.types[name] = "int"
                        elif op == '*':
                            self.values[name] = lv * rv
                            self.types[name] = "int"
                        elif op == '/':
                            self.values[name] = lv / rv
                            self.types[name] = "int"
                        elif op == '<':
                            self.values[name] = lv < rv
                            self.types[name] = "bool"
                        elif op == '<=':
                            self.values[name] = lv <= rv
                            self.types[name] = "bool"
                        elif op == '>':
                            self.values[name] = lv > rv
                            self.types[name] = "bool"
                        elif op == '>=':
                            self.values[name] = lv >= rv
                            self.types[name] = "bool"
                        elif op == '==':
                            self.values[name] = lv == rv
                            self.types[name] = "bool"
                        elif op == '!=':
                            self.values[name] = lv != rv
                            self.types[name] = "bool"
                        elif op == '<<':
                            self.values[name] = lv << rv
                            self.types[name] = "int"
                        elif op == 'and':
                            self.values[name] = lv and rv
                            self.types[name] = "bool"
                        elif op == 'or':
                            self.values[name] = lv or rv
                            self.types[name] = "bool"
                
                elif expr == "[]":
                    self.values[name] = []
                    self.types[name] = "python_list *"
                    self.list_types[name] = []

                else:
                    self.types[name], self.values[name] = self.infer_type(expr)
                    # if this is a varibale list, also copy the list types
                    if self.types[name] == 'python_list *':
                        self.values[name] = copy.deepcopy(self.values[name])
                        self.list_types[name] = copy.deepcopy(self.list_types[expr])

                new_type = self.types[name] if name in self.types else None
                if old_type and old_type != new_type:
                    sys.exit(f"Error at line {pc+1} of IR cannot change a variables type. Line: {line}")

            elif info[0] == "goto":
                pc = self.labels[info[1]]
                continue

            elif info[0] == "if":
                if len(info) == 4:
                    condition_str = info[1]
                    label = info[3]

                    if condition_str.startswith('!(') and condition_str.endswith(')'):
                        varname = condition_str[2:-1]
                        if self.infer_type(varname)[0] == "python_list *":
                            sys.exit(f"Error at line {pc+1} of IR we do not support lists in conditions. Line: {line}")
                        cond_val = self.values.get(varname)
                        if not cond_val:
                            pc = self.labels[label]
                            continue
                # condition is boolean binary operation
                else: # how to handle boolean operations CHECKPOINT
                    op = info[2]
                    lv = info[1].strip('!(')
                    rv = info[3].strip(')')
                    label = info[5]

                    lv_type, lv = self.infer_type(lv)
                    rv_type, rv = self.infer_type(rv)

                    if lv_type != rv_type:
                        sys.exit(f"Error at line {pc+1} of IR: trying to combine 2 different types. Line: {line}")
                    
                    result = False
                    
                    if lv_type == "int":
                        if op == '<':
                            result = lv < rv
                        elif op == '<=':
                            result = lv <= rv
                        elif op == '>':
                            result = lv > rv
                        elif op == '>=':
                            result = lv >= rv
                        elif op == '==':
                            result = lv == rv
                        elif op == '!=':
                            result = lv != rv
                    if rv_type == "bool":
                        if op == 'and':
                            result = lv and rv
                        elif op == 'or':
                            result= lv or rv
                    
                    if not result:
                        pc = self.labels[label]
                        continue
                    
            elif info[0] == "PushParam":
                type, value = self.infer_type(info[1])
                list_types =  self.list_types[info[1]] if info[1] in self.list_types else None
                self.pending_params.append((type, value, list_types))
            elif info[0] == "PopParams":
                n = int(info[1])
                for _ in range(n):
                    self.param_stack.pop()
            elif info[0] == "FuncCall":
                self.param_stack.append(self.pending_params)
                self.pending_params = []
                func_label = info[1]
                return_pc = pc + 1
                self.call_stack.append(return_pc)

                self.funcs.append(func_label)
                
                func_pc = self.labels[func_label]
                pc = func_pc + 1
                continue
            elif info[0] == "Param":
                # take vlaue, also keep track to remove at end of function and possible replacce
                var_name = info[1]
                self.param_name_stack[-1].append(var_name)
                # incorrect, should be lifo not fifo
                param_info = self.param_stack[-1][self.param_index]
                self.param_index += 1
                # if it shadows, move original type, value and list into shadowed version, then delete them
                if var_name in self.values:
                    self.variable_types_shadow_stack[-1][var_name] = self.types[var_name]
                    del self.types[var_name]
                    self.variable_values_shadow_stack[-1][var_name] = self.values[var_name]
                    del self.values[var_name]
                    self.variable_lists_shadow_stack[-1][var_name] = self.list_types[var_name]
                    del self.list_types[var_name]

                # then add the parameter to the type, value, and list globals based on whats in the param_stack
                self.types[var_name] = param_info[0]
                self.values[var_name] = param_info[1]
                self.list_types[var_name] = param_info[2]

            elif info[0] == "BeginFunc":
                self.param_index = 0
                self.param_name_stack.append([])
                self.variable_types_shadow_stack.append(self.types)
                self.variable_values_shadow_stack.append(self.values)
                self.variable_lists_shadow_stack.append(self.list_types)
                self.types = {}
                self.values = {}
                self.list_types = {}

            elif info[0] == "EndFunc":
                curr_func_name = self.funcs.pop()
                if curr_func_name not in self.func_types:
                    self.func_types[curr_func_name] = self.types
                elif self.func_types[curr_func_name] != self.types:
                    sys.exit(f"Error at line {pc+1} of IR: variable in function changed types between runs. Line: {line}")

                self.types = self.variable_types_shadow_stack.pop()
                self.values = self.variable_values_shadow_stack.pop()
                self.list_types = self.variable_lists_shadow_stack.pop()
                pc = self.call_stack.pop()
            
            elif info[0] == "Append":
                lst_var = info[1]
                if lst_var not in self.types:
                    sys.exit(f"Error at line {pc+1} of IR: list variable does not exist. Line: {line}")
                if self.types[lst_var] != "python_list *":
                    sys.exit(f"Error at line {pc+1} of IR: cannot append to a non-list. Line: {line}")
                new_type, new_value = self.infer_type(info[2])

                self.values[lst_var].append(new_value)
                self.list_types[lst_var].append(new_type)
                           
            elif info[0] == "Remove":
                lst_var = info[1]
                if lst_var not in self.types:
                    sys.exit(f"Error at line {pc+1} of IR: list variable does not exist. Line: {line}")
                if self.types[lst_var] != "python_list *":
                    sys.exit(f"Error at line {pc+1} of IR: cannot remove from a non-list. Line: {line}")
                removed_value = self.infer_type(info[2])[1]

                found_index = self.values[lst_var].index(removed_value)
                if found_index == -1:
                    sys.exit(f"Error at line {pc+1} of IR: element not in list. Line: {line}")
                self.values[lst_var].pop(found_index)
                self.list_types[lst_var].pop(found_index)

            elif info[0] == "Pop":
                if len(info) == 3:
                    lst_var = info[1]
                    if lst_var not in self.types:
                        sys.exit(f"Error at line {pc+1} of IR: list variable does not exist. Line: {line}")
                    if self.types[lst_var] != "python_list *":
                        sys.exit(f"Error at line {pc+1} of IR: cannot pop from a non-list. Line: {line}")
                    if self.infer_type(info[2])[0] != "int":
                        sys.exit(f"Error at line {pc+1} of IR: index is not int. Line: {line}")
                    removed_index = self.infer_type(info[2])[1]

                    if removed_index >= len(self.values[lst_var]):
                        sys.exit(f"Error at line {pc+1} of IR: pop index exceeds list size. Line: {line}")

                    self.values[lst_var].pop(removed_index)
                    self.list_types[lst_var].pop(removed_index)  

            pc += 1

        return self.types, self.func_types, self.list_types
