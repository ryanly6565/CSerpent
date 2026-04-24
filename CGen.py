from ir_interpreter import IR_Interpret
import sys

class TargetGenerator:
    tempCounter = 0
    def __init__(self):
        self.c_code = []
        self.declared_vars = {} # stores name and type
        self.func_ret_types = {} # this is for return values, because scope makes declared vars dissapear
        self.indent = 1

        self.global_types = {}
        self.global_func_types = {}
        self.global_list_types = {}
        self.curr_func = None
        

    def emit(self, code, indent=None):
        level = indent if indent is not None else self.indent
        self.c_code.append("    " * level + code)

    def emit_raw(self, code):
        self.c_code.append(code)

    def emit_list_struct(self, noOpt4=False):
        if (noOpt4):
            with open("python_list_struct.c", "r") as f:
                for line in f:
                    self.emit_raw(line.rstrip("\n"))
        else:
            with open("python_list_struct_optimized.c", "r") as f:
                for line in f:
                    self.emit_raw(line.rstrip("\n"))

    def get_new_temp_var(self):
        self.tempCounter += 1
        return "_tmp" + str(self.tempCounter)

    def infer_type(self, val):
        """Infer C type from a value string"""
        if val in ('True', 'False'):
            return 'bool'
        if val.lstrip('-').isdigit():
            return 'int'
        # look up known variable type
        if val == '[]':
            return 'python_list *'
        
        if self.curr_func:
            if val not in self.global_func_types[self.curr_func]:
                return "void *"
            return self.global_func_types[self.curr_func][val]
        else:
            if val not in self.global_types:
                return "void *"
            return self.global_types[val]

    def declare_or_assign(self, name, val, expr=None, t=None):
        """Emit declaration on first use, assignment after"""
        c_expr = expr if expr else val
        # convert Python bools to C
        c_expr = c_expr.replace('True', 'true').replace('False', 'false')

        if name not in self.declared_vars:
            t = self.infer_type(val) if not t else t

            self.declared_vars[name] = t
            if (t != "python_list *"):
                self.emit(f"{t} {name} = {c_expr};")
            else:
                # for freeing, remove any _tN variables that are taken over (so no double free)
                if val in self.declared_vars:
                    self.emit(f"{t} {name} = {val};")
                    self.emit(f"python_list_retain({name});")
                    if isinstance(val, str):
                        if val.startswith("_t"):
                            self.declared_vars.pop(val)
                else:
                    self.emit(f"{t} {name} = python_list_new();")


        else:
            # dont reset and assign if a variable
            t = self.infer_type(val) if not t else t
            if (t != "python_list *" or val in self.declared_vars.keys()):
                if t != "python_list *":
                    self.emit(f"{name} = {c_expr};")
                else:
                    # release old value
                    self.emit(f"python_list_release({name});")

                    # assign new value
                    self.emit(f"{name} = {c_expr};")

                    # retain new value if it's a variable
                    if val in self.declared_vars:
                        self.emit(f"python_list_retain({name});")
            else:
                # RYAN: IF USED TO EXIST, FREE??????
                self.emit(f"python_list_release({name});")
                self.emit(f"{name} = python_list_new();")

    def parse_blocks(self, ir_lines):
        """Convert IR into structured blocks"""
        ir_lines = [l.strip() for l in ir_lines if l.strip()]
        i = 0
        blocks = []

        while i < len(ir_lines):
            line = ir_lines[i]
            info = line.split()

            # function declaration
            if info[0] == 'goto' and i + 1 < len(ir_lines) and not ir_lines[i+1].strip().startswith('_L'):
                skip_label = info[1]
                i += 1
                func_name = ir_lines[i].rstrip(':')
                i += 1  # skip BeginFunc
                i += 1
                params = []
                body_lines = []
                ret_expr = None
                while i < len(ir_lines) and ir_lines[i] != 'EndFunc':
                    if ir_lines[i].startswith('Param '):
                        params.append(ir_lines[i].split()[1])
                    elif ir_lines[i].startswith('ret :='):
                        ret_expr = ir_lines[i].split(' := ')[1].strip()
                    else:
                        body_lines.append(ir_lines[i])
                    i += 1
                i += 1  # skip EndFunc
                i += 1  # skip skip_label:
                pushed = self.func_call_params.get(func_name, [])

                # param types take from the dynamic function run now, python dicts to lists preserve insertion order
                param_types = list(self.global_func_types[func_name].values())[:len(pushed)]
                blocks.append({'type': 'func', 'name': func_name, 'params': params, 'param_types': param_types, 'body': body_lines, 'ret': ret_expr})

            # if statement
            elif info[0] == 'if':
                cond = line.split("if", 1)[1].split("goto", 1)[0].strip()
                if cond.startswith("!(") and cond.endswith(")"):
                    cond = cond[2:-1]
                cond = cond.replace(" and ", " && ").replace(" or ", " || ")
                else_label = info[-1] if len(info) > 3 else None  # safe check

                i += 1
                true_body = []
                depth = 0
                while i < len(ir_lines):
                    current = ir_lines[i]
                    current_info = current.split()
                    if current_info and current_info[0] == 'if':
                        depth += 1
                    if current.startswith('goto') and depth == 0:
                        break
                    if current == f'{else_label}:':
                        break
                    if current.endswith(':') and current.startswith('_L'):
                        depth = max(0, depth - 1)
                    true_body.append(current)
                    i += 1

                end_label = ir_lines[i].split()[1] if i < len(ir_lines) and len(ir_lines[i].split()) > 1 else None
                if i < len(ir_lines):
                    i += 1  # skip goto _L2
                if i < len(ir_lines):
                    i += 1  # skip _L1:

                false_body = []
                while i < len(ir_lines) and end_label and ir_lines[i] != f"{end_label}:":
                    false_body.append(ir_lines[i])
                    i += 1

                if i < len(ir_lines):
                    i += 1  # skip _L2:

                blocks.append({'type': 'if', 'cond': cond, 'true': true_body, 'false': false_body})

                        # for loop detection: var ASSIGNMENT + 
            # LABEL +
            # IF CONDITION
            elif (':=' in line and i + 2 < len(ir_lines)
                and ir_lines[i+1].endswith(':') and ir_lines[i+1].startswith('_L')
                and ir_lines[i+2].startswith('if')):
                    # ASSIGNMENT var := init 
                    assign_parts = line.split(' := ')
                    var = assign_parts[0]
                    init = assign_parts[1]
                
                    # LABEL _L1
                    start_label = ir_lines[i+1].rstrip(':')  
                
                    #IF CONDITION: if !(var < limit) goto end_label
                    if_line = ir_lines[i+2]
                     #split line from right and left parenthese to get condition
                    cond = if_line.split('(')[1].split(')')[0] 
                
                    #LABEL
                    end_label = if_line.split()[-1]              # "_L2"
                    i += 3  # skip init, label, if lines.
                
                    #BODY UNTIL goto start_label
                    body_lines = []
                    while i < len(ir_lines) and ir_lines[i] != f"goto {start_label}":
                        body_lines.append(ir_lines[i])
                        i += 1

                    # INCREMENT last Line last
                    increment = body_lines.pop()
                    i += 1  # skip "goto _L1"
                    i += 1  # skip "_L2:"
                    blocks.append({'type': 'for', 'var': var, 'init': init, 'cond': cond, 'increment': increment, 'body': body_lines})

            else:
                blocks.append({'type': 'stmt', 'line': line})
                i += 1

        return blocks

    def gen_blocks(self, blocks):
        """Generate C code from structured blocks"""
        for block in blocks:
            if block['type'] == 'func':
                self.gen_func(block)
            elif block['type'] == 'if':
                self.gen_if(block)
            elif block['type'] == 'for':
                self.gen_for(block)
            else:
                self.gen_stmt(block['line'])

    def gen_func(self, block):
        """Generate C function"""
        self.curr_func = block['name']
        # populate declared_vars with param types FIRST
        for i, param in enumerate(block['params']):
            t = block['param_types'][i] if i < len(block['param_types']) else 'int'
            self.declared_vars[param] = t

        # parse and generate body first so declared_vars gets populated
        inner_blocks = self.parse_blocks(block['body'])
        
        # temporarily collect body code
        old_c_code = self.c_code
        self.c_code = []
        self.indent = 1
        self.gen_blocks(inner_blocks)
        body_code = self.c_code
        self.c_code = old_c_code

        # NOW infer ret type since declared_vars is populated
        ret_type = 'void'
        if block['ret'] and block['ret'] != 'None':
            ret_type = self.infer_type(block['ret'])

        # store for use in main when we see _t1 := ret
        self.func_ret_types[block['name']] = ret_type

        # build signature
        init = f"{ret_type} {block['name']}("
        for i in range(len(block['params'])):
            if i != len(block['params']) - 1:
                init += f"{block['param_types'][i]} {block['params'][i]}, "
            else:
                init += f"{block['param_types'][i]} {block['params'][i]}) {{"
        if not block['params']:
            init += ") {"
        self.emit_raw(init)

        # emit body
        self.c_code.extend(body_code)

        # emit return
        if block['ret']:
            ret_val = block['ret'].replace('True', 'true').replace('False', 'false')
            if ret_val != 'None':
                self.emit(f"return {ret_val};")
            else:
                self.emit("return;")

        self.emit_raw("}")
        self.emit_raw("")
        self.curr_func = None

    def gen_if(self, block):
        cond = block['cond'].replace('True', 'true').replace('False', 'false').replace(" and ", " && ").replace(" or ", " || ")

        before_vars = set(self.declared_vars.keys())

        self.emit(f"if ({cond}) {{")
        self.indent += 1

        # true branch, save new variables
        saved = self.declared_vars.copy()
        true_blocks = self.parse_blocks(block['true'])
        self.gen_blocks(true_blocks)
        true_vars = set(self.declared_vars.keys())

        self.indent -= 1
        self.declared_vars = saved

        # false branch, save new variables
        false_vars = set(saved.keys())

        if block['false']:
            self.emit("} else {")
            self.indent += 1

            false_blocks = self.parse_blocks(block['false'])
            self.gen_blocks(false_blocks)
            false_vars = set(self.declared_vars.keys())

            self.indent -= 1

        self.emit("}")

        true_new = true_vars - before_vars
        false_new = false_vars - before_vars

        shared = true_new & false_new
        if shared:
            sys.exit(f"Error: We do not allow two variables with the same name in different branches unless they were defined before the conditional. Variable(s) are:{', '.join(shared)}")

        # restore original scope
        self.declared_vars = saved

    def gen_for(self, block):
        """Generate C for loop from for block"""
        var = block['var']
        init = block['init']
        cond = block['cond']
        # increment is of the form "i := i + 5"
        inc_parts = block['increment'].split(' := ')
        #convert to "i = i + 5"
        inc_expr = f"{inc_parts[0]} = {inc_parts[1]}"

        # MARK var in Declared vars dictionary 
        self.declared_vars[var] = 'int'

        # construction of c expression
        self.emit(f"for (int {var} = {init}; {cond}; {inc_expr}) {{")
        self.indent += 1

        body_blocks = self.parse_blocks(block['body'])
        self.gen_blocks(body_blocks)

        self.indent -= 1
        self.emit("}")

    def gen_stmt(self, line):
        """Generate a single C statement"""
        info = line.split()

        # print
        if info[0] == 'Print':
            var = info[1].replace('True', 'true').replace('False', 'false')
            t = self.declared_vars.get(var, 'None')
            if t == 'None':
                t = self.infer_type(var.replace('true', 'True').replace('false', 'False'))
            if t == 'int':
                fmt = '%d' if t == 'int' else '%d'
                self.emit(f'printf("{fmt}\\n", {var});')
            elif t == 'bool':
                self.emit(f"if ({var}) printf(\"True\\n\"); else printf(\"False\\n\");")
            elif t == 'python_list *':
                temp_var = self.get_new_temp_var()
                self.emit(f"char *{temp_var} = python_list_to_string({var});")
                self.emit(f"printf(\"%s\\n\", {temp_var});")
                self.emit(f"free({temp_var});")
        
        # function stuff
        elif info[0] == 'PushParam':
            if not hasattr(self, 'current_call_params'):
                self.current_call_params = []
            self.current_call_params.append(info[1])
        elif info[0] == 'FuncCall':
            params = getattr(self, 'current_call_params', [])
            param_str = ', '.join(params)
            self.last_func_call = f"{info[1]}({param_str})"
            self.current_call_params = []

        # list appending
        elif info[0] == "Append":
            var = info[1].replace('True', 'true').replace('False', 'false')
            value = info[2]
            type = self.infer_type(value)
            type = 0 if (type == 'int') else (1 if type == 'bool' else 2)

            if type == 0 or type == 1:
                self.emit(f"python_list_append({var}, {type}, (void*)(long) {value});")
            else:
                if isinstance(value, str):
                    if value.startswith("_t"):
                        self.declared_vars.pop(value)
                self.emit(f"python_list_append({var}, {type}, {value});")

        # list removing
        elif info[0] == "Remove":
            var = info[1].replace('True', 'true').replace('False', 'false')
            value = info[2]
            type = self.infer_type(value)
            type = 0 if (type == 'int') else (1 if type == 'bool' else 2)

            self.emit(f"python_list_remove({var}, {type}, (void*) {value});")

        elif info[0] == "Pop":
            lst = info[1]
            idx = info[2]
            temp_var = self.get_new_temp_var()

            self.emit(f"python_list_element {temp_var} = python_list_pop({lst}, {idx});")
            self.emit(f"if ({temp_var}.type == 2) {{")
            self.emit(f"    python_list_release((python_list *) {temp_var}.value);")
            self.emit(f"}}")
            
        # assignment
        elif ':=' in line:
            parts = line.split(' := ')
            name = parts[0].strip()
            val = parts[1].strip()

            # binary op e.g. _t1 + 3
            if len(val.split()) == 3 and val.split()[0] != "Pop":
                left, op, right = val.split()
                bool_ops = {'>=', '<=', '>', '<', '==', '!=', 'and', 'or'}
                op_map = {'and': '&&', 'or': '||'}
                c_op = op_map.get(op, op)
                if op in bool_ops:
                    self.declare_or_assign(name, 'True', f"{left} {c_op} {right}")
                else:
                    self.declare_or_assign(name, left, f"{left} {c_op} {right}")

            # unary op e.g. -10
            elif val.startswith('-') and not val[1:].lstrip('-').isdigit() == False and len(val) > 1:
                self.declare_or_assign(name, val, val)

            # return call of a function
            elif val == 'ret':
                func_call = getattr(self, 'last_func_call', 'unknown()')
                func_name = func_call.split('(')[0]
                t = self.func_ret_types.get(func_name, 'int')
                self.declared_vars[name] = t
                self.emit(f"{t} {name} = {func_call};")

                if t == "python_list *":
                    self.emit(f"python_list_retain({name});")

            # return length of function
            elif val.startswith('Length'):
                self.declare_or_assign(name, val=f"{val.split()[1]}->size", t="int")

            # return popped object
            elif val.startswith('Pop'):
                if self.curr_func:
                    my_type = self.global_func_types[self.curr_func][name]
                else:
                    my_type = self.global_types[name]
                
                pop_expr = f"python_list_pop({val.split()[1]}, {val.split()[2]})"
                
                if my_type == 'int':
                    cast_expr = f"(int)(long) {pop_expr}.value"
                elif my_type == 'bool':
                    cast_expr = f"(bool)(long) {pop_expr}.value"
                elif my_type == 'python_list *':
                    cast_expr = f"(python_list *) {pop_expr}.value"
                else:
                    cast_expr = f"({my_type})(long) {pop_expr}.value"

                if name in self.declared_vars:
                    self.emit(f"{name} = {cast_expr};")
                else:
                    self.declared_vars[name] = my_type
                    self.emit(f"{my_type} {name} = {cast_expr};")
            else:
                self.declare_or_assign(name, val)

    def generate(self, ir_lines, noOpt4=False, noOpt5=True):
        """Main entry: convert IR lines to C"""
        ir_lines = [l.strip() for l in ir_lines if l.strip()]

        interpreter = IR_Interpret(ir_lines)
        self.global_types, self.global_func_types, self.global_list_types = interpreter.run()

        # first pass: collect PushParam values per FuncCall
        self.func_call_params = {}
        current_params = []
        for line in ir_lines:
            info = line.strip().split()
            if not info:
                continue
            if info[0] == 'PushParam':
                current_params.append(info[1])
            elif info[0] == 'FuncCall':
                self.func_call_params[info[1]] = current_params
                current_params = []

        # separate functions from main body
        func_blocks = []
        main_lines = []
        i = 0
        while i < len(ir_lines):
            line = ir_lines[i]
            info = line.split()
            if info[0] == 'goto' and i + 1 < len(ir_lines):
                next_line = ir_lines[i+1].strip()
                if next_line.endswith(':') and not next_line.startswith('_L'):
                    end_skip = info[1]
                    func_ir = []
                    while i < len(ir_lines) and ir_lines[i] != f"{end_skip}:":
                        func_ir.append(ir_lines[i])
                        i += 1
                    if i < len(ir_lines):
                        i += 1
                    func_blocks.append(func_ir)
                    continue
            main_lines.append(line)
            i += 1

        # emit includes
        self.emit_raw("#include <stdio.h>")
        self.emit_raw("#include <stdbool.h>")
        isList = False
        for line in ir_lines:
            if "[]" in line:
                isList = True
        if (not noOpt5 and isList):
            self.emit_list_struct(noOpt4=noOpt4)
        if noOpt5:
            self.emit_list_struct(noOpt4=noOpt4)
        self.emit_raw("")

        # emit functions first
        for func_ir in func_blocks:
            blocks = self.parse_blocks(func_ir)
            self.gen_blocks(blocks)
            self.declared_vars = {}
        
        # emit main
        self.emit_raw("int main() {")
        self.indent = 1
        main_blocks = self.parse_blocks(main_lines)
        self.gen_blocks(main_blocks)
        self.emit_frees()
        self.emit_raw("    return 0;")
        self.emit_raw("}")

    def emit_frees(self):
        for var in self.declared_vars.keys():
            if self.declared_vars[var] == 'python_list *':
                self.emit(f"python_list_release({var});")
                
    def print_code(self):
        for line in self.c_code:
            print(line)