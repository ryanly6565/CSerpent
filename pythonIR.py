# Much of this was taken from tutorial code
class IRGenerator:
    """
    Generates Three-Address Code from an AST using the visitor pattern.
    Based on the tinyJava IRGen implementation.
    """
    
    def __init__(self):
        self.ir_code = []           # List of generated IR instructions
        self.temp_counter = 0       # Counter for temporary variables
        self.label_counter = 0      # Counter for labels
    
    def emit(self, code):
        """Add an instruction to the IR"""
        self.ir_code.append("    " + code)
    
    def emit_label(self, label):
        """Add a label marker"""
        self.ir_code.append(f"{label}:")
    
    def new_temp(self):
        """Generate a new temporary variable name"""
        self.temp_counter += 1
        return f"_t{self.temp_counter}"
    
    def reset_temps(self):
        """Reset temporary counter (optional, between statements)"""
        self.temp_counter = 0
    
    def new_label(self):
        """Generate a new label name"""
        self.label_counter += 1
        return f"_L{self.label_counter}"
    
    def generate(self, node):
        """Dispatch to appropriate generator method"""
        method_name = f"gen_{node['type']}"
        method = getattr(self, method_name, self.gen_default)
        return method(node)
    
    def gen_default(self, node):
        """Default handler for unknown node types"""
        print(f"  Warning: No handler for {node['type']}")
        return None
    
    # ----- Expression Generators -----
    def gen_None(self, node):
        """None literal"""
        return 'None'
    
    def gen_Constant(self, node):
        """Constants return their value directly"""
        return str(node['value'])
    
    def gen_Variable(self, node):
        """Variables return their name"""
        return node['name']
    
    def gen_UnaryOp(self, node):
        """Unary operation: generates stuff like temp := -10"""
        operand = self.generate(node['operand'])
        temp = self.new_temp()
        self.emit(f"{temp} := {node['op']}{operand}")
        return temp    
    
    def gen_BinOp(self, node):
        """Binary operation: generates temp := left op right"""
        left = self.generate(node['left'])
        right = self.generate(node['right'])
        temp = self.new_temp()
        self.emit(f"{temp} := {left} {node['op']} {right}")
        return temp
    
    # ----- Statement Generators -----
    
    def gen_AssignStmt(self, node):
        """Assignment statement"""
        if node['expr']['type'] == 'PopStmt':
            expr_result = self.gen_PopStmt(node['expr'], used=True)
        else:
            expr_result = self.generate(node['expr'])
        self.emit(f"{node['name']} := {expr_result}")
        # self.reset_temps()
    
    def gen_IfStmt(self, node):
        """If-else statement with labels and jumps"""

        cond_node = node['condition']

        # If the condition is a binary op, emit directly like the for loop
        if cond_node['type'] == 'BinOp':
            left = self.generate(cond_node['left'])
            right = self.generate(cond_node['right'])
            cond = f"{left} {cond_node['op']} {right}"
        else:
            cond = self.generate(cond_node)

        else_label = self.new_label()
        end_label = self.new_label()

        self.emit(f"if !({cond}) goto {else_label}")

        for stmt in node.get('true_body', []):
            self.generate(stmt)

        self.emit(f"goto {end_label}")

        self.emit_label(else_label)

        for stmt in node.get('false_body', []):
            self.generate(stmt)

        self.emit_label(end_label)
        
    def gen_List(self, node):
        """List literal: allocates and populates a list"""
        temp = self.new_temp()
        self.emit(f"{temp} := []")
        for element in node.get('elements', []):
            val = self.generate(element)
            self.emit(f"Append {temp} {val}")
        return temp
    
    def gen_FuncCall(self, node):
        """Function call with parameters"""
        # Push all arguments
        for arg in node.get('args', []):
            arg_result = self.generate(arg)
            self.emit(f"PushParam {arg_result}")
        
        # Call the function
        self.emit(f"FuncCall {node['name']}")
        
        # Clean up parameters
        self.emit(f"PopParams {len(node.get('args', []))}")
        
        # Get return value into a temp
        temp = self.new_temp()
        self.emit(f"{temp} := ret")
        return temp
    
    def gen_MethodDecl(self, node):
        """Method/function declaration"""
        skip_label = self.new_label()
        
        # Skip function body until called
        self.emit(f"goto {skip_label}")
        
        # Function label
        self.emit_label(node['name'])
        
        # Function prologue
        self.emit("BeginFunc")

        # Emit parameters
        for param in node.get('params', []):
            self.emit(f"Param {param['name']}")
        
        # Generate body statements
        for stmt in node.get('body', []):
            self.generate(stmt)
        
        # Generate return
        if node.get('return_expr'):
            ret_val = self.generate(node['return_expr'])
            self.emit(f"ret := {ret_val}")
        
        # Function epilogue
        self.emit("EndFunc")
        
        # Skip label (execution continues here)
        self.emit_label(skip_label)
    
    def gen_PrintStmt(self, node):
        """Print statement"""
        expr_result = self.generate(node['expr'])
        self.emit(f"Print {expr_result}")
        # self.reset_temps()
    
    def gen_LenStmt(self, node):
        """Get length of a list"""
        list_val = self.generate(node['list'])
        temp = self.new_temp()
        self.emit(f"{temp} := Length {list_val}")
        return temp

    def gen_AppendStmt(self, node):
        """Append a value to a list"""
        list_val = self.generate(node['list'])
        val = self.generate(node['value'])
        self.emit(f"Append {list_val} {val}")
        # self.reset_temps()

    def gen_PopStmt(self, node, used=False):
        """Pop a value from a list by index"""
        list_val = self.generate(node['list'])
        index = self.generate(node['index'])

        if not used:
            # pop used as a statement, just emit the action
            self.emit(f"Pop {list_val} {index}")
            return None
        else:
            # pop used in an expression, store the result in a temp
            temp = self.new_temp()
            self.emit(f"{temp} := Pop {list_val} {index}")
            return temp

    def gen_RemoveStmt(self, node):
        """Remove a value from a list"""
        list_val = self.generate(node['list'])
        val = self.generate(node['value'])
        self.emit(f"Remove {list_val} {val}")
        # self.reset_temps()
    
    def gen_ForStmt(self, node):
        """For loop: for var in range(a1, a2, a3)"""
        # Set up labels
        start_label = self.new_label()
        end_label = self.new_label()

        # Get range values, using defaults if None
        a1 = self.generate(node['a1']) if node.get('a1') else '0'
        a2 = self.generate(node['a2'])
        a3 = self.generate(node['a3']) if node.get('a3') else '1'

        var = node['var']

        # Initialize loop variable
        self.emit(f"{var} := {a1}")

        # Loop start
        self.emit_label(start_label)

        # Check condition
        self.emit(f"if !({var} < {a2}) goto {end_label}")

        # Generate body
        for stmt in node.get('body', []):
            self.generate(stmt)

        # Increment
        self.emit(f"{var} := {var} + {a3}")
        self.emit(f"goto {start_label}")

        # End label
        self.emit_label(end_label)
        # self.reset_temps()

    def gen_Program(self, node):
        """Generate IR for entire program"""
        for stmt in node.get('statements', []):
            self.generate(stmt)
        


    
    def print_ir(self):
        """Print all generated IR code"""
        print("Generated IR:")
        print("-" * 40)
        for line in self.ir_code:
            print(line)
        print("-" * 40)

