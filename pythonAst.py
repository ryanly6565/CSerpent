# Note: A large chunk of this code was taken from tutorial code

class Node:
    """
    Base class for all AST nodes.
    Every node must implement children() to return its child nodes.
    """
    def children(self):
        """Return a list of (name, node) tuples for all children"""
        pass
    
    attr_names = ()  # Attributes to display when printing

class Program(Node):
    """
    Program node
    
    Attributes:
        statements: List of Nodes that represent the program statements
    """
    def __init__(self, statements):
        self.statements = statements
    
    def __repr__(self):
        return f"Program statements={self.statements})"

    def children(self):
        return_statements = []
        count = 1
        for statement in self.statements:
            return_statements.append((f"statement_{count}", statement))
            count+=1
        return return_statements

    attr_names = ()
    
class UnaryOp(Node):
    """
    Unary operation node (not, -)

    Attributes:
        op: The operator (string)
        operand: The thing being operated on (Node)
    """
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand
    
    def __repr__(self):
        return f"{self.op} {self.operand}"

    def children(self):
        return (('operand', self.operand),)

    attr_names = ('op',)

class BinOp(Node):
    """
    Binary operation node (+, -, *, //, and, or, >, <, >=, <=, ==, !=)
    
    Attributes:
        op: The operator (string)
        left: Left operand (Node)
        right: Right operand (Node)
    """
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"{self.left} {self.op} {self.right}"
    
    def children(self):
        nodelist = []
        if self.left is not None:
            nodelist.append(('left', self.left))
        if self.right is not None:
            nodelist.append(('right', self.right))
        return tuple(nodelist)
    
    attr_names = ('op',)

class Constant(Node):
    """
    Constant value node (integers, booleans, identifiers)
    
    Attributes:
        type: Type of constant ('int', 'bool', 'id')
        value: The actual value
    """
    def __init__(self, type, value):
        self.type = type
        self.value = value
    
    def __repr__(self):
        return f"{self.type} {self.value}"
    
    def children(self):
        return ()  # Constants have no children
    
    attr_names = ('type', 'value')

class AssignStmt(Node):
    """
    Assignment statement node
    
    Attributes:
        name: Variable name (string)
        expr: Expression being assigned (Node)
    """
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr
    
    def __repr__(self):
        return f"{self.name} = {self.expr}"
    
    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ('name',)

class IfStmt(Node):
    """
    If statement node

    Attributes:
        condition: Boolean expression (Node)
        body: Statement(s) to execute if true (Node)
        orelse: Statement(s) to execute if condition is false (Node)
    """
    def __init__(self, condition, body, orelse=None):
        self.condition = condition
        self.body = body
        if isinstance(orelse, list):
            self.orelse = orelse
        elif orelse:
            self.orelse = [orelse]
        else:
            self.orelse = orelse

    def __repr__(self):
        s = f"if {self.condition}:\n"
        for stmt in self.body:
            s += f"    {stmt}\n"

        if self.orelse:
            s += "else:\n"

        return s.rstrip()

    def children(self):
        nodelist = []

        nodelist.append(('condition', self.condition))

        statement_list = []
    
        for i, statement in enumerate(self.body):
            statement_list.append((f"statement_{i+1}", statement))

        nodelist.append(('statements', statement_list))

        if self.orelse is not None:
            orelse_statement_list = []

            for i, orelse_statement in enumerate(self.orelse):
                orelse_statement_list.append((f"statement_{i+1}", orelse_statement))

            nodelist.append(('orelse', orelse_statement_list))

        return tuple(nodelist)

    attr_names = ()

class Return(Node):
    """
    Function return node:

    Attributes:
        value: the value being returned (Node)
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"return {self.value}"

    def children(self):
        return (('return', self.value),)
    
    attr_names = ()

class Parameter(Node):
    """
    Function parameter node.
    
    Attributes:
        name: The parameter name (string)
    """
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def children(self):
        return ()
    
    attr_names = ('name',)

class ForStmt(Node):
    """
    For loop node, specifically the format below
        For i in range(a1, a2, a3):
            statements

    Attributes:
        var: loop variable name (string)
        a1: starting count (Node)
        a2: ending count (Node)
        a3: skip count (Node)
        body: list of statements (Nodes)
    """
    def __init__(self, var, a2, body, a1=0, a3=1):
        self.var = var
        if not isinstance(body, list):
            self.body = [body]
        else:
            self.body = body
        self.a2 = a2
        self.a1 = a1
        self.a3 = a3

    def __repr__(self):
        return f"for {self.var} in range({self.a1}, {self.a2}, {self.a3}): {self.body}"

    def children(self):
        nodelist = [('a1', self.a1), ('a2', self.a2), ('a3', self.a3)]
        body_list = []
        for i, statement in enumerate(self.body):
            body_list.append((f"statement_{i+1}", statement))

        nodelist.append(('Body Statements', body_list))
        return tuple(nodelist)

    attr_names = ('var',)

class Function(Node):
    """
    Function definition node.

    Attributes:
        name: The name of the function (string)
        params: The parameters of the function (Parameters)
        body: The list of statements in the function body (Nodes)
    """
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        if not isinstance(body, list):
            self.body = [body]
        else:
            self.body = body
    
    def __repr__(self):
        params_str = ", ".join(str(param) for param in self.params)
        lines = [f"def {self.name}({params_str}):"]

        for stmt in self.body:
            lines.append(f"    {stmt}")

        return "\n".join(lines)
    
    def children(self):
        nodelist = []

        nodelist.append(('name', self.name)) 

        if self.params is not None:
            param_list = []
            for i, param in enumerate(self.params):
                param_list.append((f"param_{i+1}", param))

            nodelist.append(('params', param_list))

        body_list = []
        for i, statement in enumerate(self.body):
            body_list.append((f"statement_{i+1}", statement))

        nodelist.append(('Body Statements', body_list))

        return tuple(nodelist)

    attr_names = ()

class PrintStmt(Node):
    """
    Print statement node.

    Attributes:
        expr: The expression to print (Node)
    """
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"print({self.expr})"

    def children(self):
        return (('expr', self.expr),)

    attr_names = ()

class LenStmt(Node):
    """
    Len statement node for lists.

    Attributes:
        contained_list: The list (Node)
    """
    def __init__(self, contained_list):
        self.contained_list = contained_list

    def __repr__(self):
        return f"len({self.contained_list})"

    def children(self):
        return (('contained_list', self.contained_list),)

    attr_names = ()

class AppendStmt(Node):
    """
    Append statement node for lists.

    Attributes:
        list1: The list (Node)
        value: The value being appended (Node)
    """
    def __init__(self, list1, value):
        self.list1 = list1
        self.value = value

    def __repr__(self):
        return f"append({self.list1} + {self.value})"

    def children(self):
        return (('contained_list', self.list1), ('value', self.value))

    attr_names = ()

class PopStmt(Node):
    """
    Pop statement node for lists.

    Attributes:
        contained_list: The list (Node)
        index: The index which we want to pop (Node)
    """
    def __init__(self, contained_list, index):
        self.contained_list = contained_list
        self.index = index

    def __repr__(self):
        return f"pop({self.contained_list}, {self.index})"

    def children(self):
        return (('contained_list', self.contained_list), ('index', self.index))

class RemoveStmt(Node):
    """
    Remove statement node for lists.

    Attributes:
        contained_list: The list (Node)
        value: The value which we want to remove (Node)
    """
    def __init__(self, contained_list, value):
        self.contained_list = contained_list
        self.value = value

    def __repr__(self):
        return f"remove({self.contained_list}, {self.value})"

    def children(self):
        return (('contained_list', self.contained_list), ('value', self.value))

class List(Node):
    """
    Function definition node.

    Attributes:
        elements: The elements contained by the list (Node)
    """
    def __init__(self, elements=None):
        if (not elements):
            self.contents = []
        elif (isinstance(elements, list)):
            self.contents = elements
        else:
            self.contents = [elements]
    
    def __repr__(self):
        return "[" + ", ".join(str(elem) for elem in self.contents) + "]"

    def children(self):
        nodelist = []
        valList = []
        for i, val in enumerate(self.contents):
            valList.append((f"value_{i+1}", val))
        nodelist.append(("Values", valList))
        return tuple(nodelist)

    attr_names = ('contents',)

class CallFunction(Node):
    """
    Function call node

    Attributes:
        func: Name of the function being called (Node)
        args: List of arguments (Nodes)
    """
    def __init__(self, func, args=[]):
        self.func = func
        self.args = args

    def __repr__(self):
        arg_str = ", ".join(str(a) for a in self.args)
        return f"{self.func}({arg_str})"

    def children(self):
        nodelist = []
        arg_list = []
        for i, arg in enumerate(self.args):
            arg_list.append((f"arg_{i+1}", arg))
        nodelist.append(("Args", arg_list))
        return tuple(nodelist)

    attr_names = ('func',)



class NoneNode(Node):
    """
    None literal node.
    Represents the `None` value in the AST.
    """

    def __init__(self):
        pass

    def __repr__(self):
        return "None"

    def children(self):
        return ()

    attr_names = ()

class NodeVisitor:
    """
    Base class for visiting AST nodes.
    
    To use: Create a subclass and define visit_X methods
    where X is the node class name (e.g., visit_BinOp)
    """
    def visit(self, node, offset=0):
        """
        Visit a node by calling its specific visit method.
        Falls back to generic_visit if no specific method exists.
        """
        if node is None:
            return None
        if isinstance(node, list):
            for item in node:
                self.visit(item, offset)
            return
        
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, offset)
    
    def generic_visit(self, node, offset=0):
        """
        Default visit method - prints node info and visits children
        """
        lead = ' ' * offset
        
        output = lead + node.__class__.__name__
        
        if node.attr_names:
            attrs = [getattr(node, n) for n in node.attr_names]
            output += ': ' + ', '.join(str(v) for v in attrs)
        
        print(output)
        
        for (child_name, child) in node.children():
            self.visit(child, offset + 2)

class PrettyPrinter(NodeVisitor):
    """Prints the AST in a readable tree format"""
     
    def visit_IfStmt(self, node, offset=0):
        lead = ' ' * offset
        print(f"{lead}IfStmt:")

        print(f"{lead}  Condition:")
        self.visit(node.condition, offset + 4)

        print(f"{lead}  Then:")
        for stmt in node.body:
            self.visit(stmt, offset + 4)

        if node.orelse is not None:
            print(f"{lead}  Else:")
            for stmt in node.orelse:
                self.visit(stmt, offset + 4)
    
    def visit_ForStmt(self, node, offset=0):
        lead = ' ' * offset
        print(f"{lead}ForStmt: {node.var}")
        
        print(f"{lead}  Range:")
        print(f"{lead}    a1: {node.a1}")
        print(f"{lead}    a2: {node.a2}")
        print(f"{lead}    a3: {node.a3}")
        
        print(f"{lead}  Body:")
        for stmt in node.body:
            self.visit(stmt, offset + 4)
    
class JsonPrinter(NodeVisitor):
    """Prints the AST in a readable JSON format"""

    def visit_Program(self, node, offset=0):
        lead = '\t' * offset
        print(f"{lead}{{")
        print(f"{lead}\tProgram: {{")
        
        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_AssignStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tAssign: {{")

        print(f"{lead}\t\tname: {node.name},")
        print(f"{lead}\t\texpression:", end="")
        self.visit(node.expr, offset + 2)
        
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_Constant(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tConstant: {{")

        print(f"{lead}\t\ttype: {node.type},")
        print(f"{lead}\t\tvalue: {node.value}")
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_List(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tList: {{")

        for child_name, child_node in node.children():
            print(f"{lead}\t\t\t{child_name}: ", end = "")
            self.visit(child_node, offset + 2)
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_UnaryOp(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tUnary Operation: {{")

        print(f"{lead}\t\toperation: {node.op},")
        print(f"{lead}\t\toperand: {node.operand}")
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_BinOp(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tBinary Operation: {{")

        print_Json(self, node, offset) 
        
        print(f"{lead}\t\toperand: {node.op}")
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_IfStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tIf Statement: {{")

        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_PrintStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tPrint Function: {{")
        
        print_Json(self, node, offset);

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_Function(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tFunction Definition: {{")
        
        print_Json(self, node, offset);
        
        print(f"{lead}\t}}")
        print(f"{lead}}}")
    
    def visit_Parameter(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tParameter: {{")

        print(f"{lead}\t\tname: {node.name},")
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_Return(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tReturn: {{")

        print(f"{lead}\t\tvalue: {node.value},")
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_CallFunction(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tCall Function: {{")

        print(f"{lead}\t\tFunction Name: {node.func}")
        print_Json(self, node, offset)
        
        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_List(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tList: {{")

        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_LenStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tLength Of: {{")

        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_AppendStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tAppend: {{")

        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_PopStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tPop: {{")

        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_RemoveStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tRemove: {{")

        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

    def visit_ForStmt(self, node, offset=0):
        lead = '\t' * offset
        print(f"{{")
        print(f"{lead}\tFor: {{")

        print_Json(self, node, offset)

        print(f"{lead}\t}}")
        print(f"{lead}}}")

# Function to run print JSON for our script
def print_Json(printer, node, offset=0):
    lead = '\t' * offset
    for child_name, child_node in node.children():
        if isinstance(child_node, Node):
            print(f"{lead}\t\t{child_name}: ", end = "")
            printer.visit(child_node, offset + 2)
        
        elif isinstance(child_node, list):
            print(f"{lead}\t\t{child_name}: {{")
            for list_child_name, list_children in child_node:
                print(f"{lead}\t\t\t{list_child_name}: ", end = "")
                printer.visit(list_children, offset + 3)
            print(f"{lead}\t\t}}")
        else:
            print(f"{lead}\t\t{child_name}: {child_node}")

class DictPrinter(NodeVisitor):
    """Converts the AST into a nested dictionary format"""

    def visit_Program(self, node, offset=0):
        return {
            'type': 'Program',
            'statements': [self.visit(s) for s in node.statements]
        }

    def visit_AssignStmt(self, node, offset=0):
        return {
            'type': 'AssignStmt',
            'name': node.name,
            'expr': self.visit(node.expr)
        }

    def visit_Constant(self, node, offset=0):
        if node.type == 'id':
            return {
                'type': 'Variable',
                'name': node.value
            }
        return {
            'type': 'Constant',
            'value': node.value
        }

    def visit_UnaryOp(self, node, offset=0):
        return {
            'type': 'UnaryOp',
            'op': node.op,
            'operand': self.visit(node.operand)
        }

    def visit_BinOp(self, node, offset=0):
        return {
            'type': 'BinOp',
            'op': node.op,
            'left': self.visit(node.left),
            'right': self.visit(node.right)
        }

    def visit_IfStmt(self, node, offset=0):
        result = {
            'type': 'IfStmt',
            'condition': self.visit(node.condition),
            'true_body': [self.visit(s) for s in node.body],
        }
        if node.orelse:
            result['false_body'] = [self.visit(s) for s in node.orelse]
        return result

    def visit_PrintStmt(self, node, offset=0):
        return {
            'type': 'PrintStmt',
            'expr': self.visit(node.expr)
        }

    def visit_Function(self, node, offset=0):
        result = {
            'type': 'MethodDecl',
            'name': node.name,
            'params': [self.visit(p) for p in node.params],
            'body': [self.visit(s) for s in node.body]
        }
        
        # Check if last statement is a Return, pull it out as return_expr
        if node.body and isinstance(node.body[-1], Return):
            result['body'] = [self.visit(s) for s in node.body[:-1]]
            result['return_expr'] = self.visit(node.body[-1].value)
        
        return result

    def visit_Parameter(self, node, offset=0):
        return {
            'type': 'Parameter',
            'name': node.name
        }

    def visit_Return(self, node, offset=0):
        return {
            'type': 'Return',
            'value': self.visit(node.value)
        }

    def visit_CallFunction(self, node, offset=0):
        return {
            'type': 'FuncCall',
            'name': node.func,
            'args': [self.visit(a) for a in node.args]
        }

    def visit_List(self, node, offset=0):
        return {
            'type': 'List',
            'elements': [self.visit(e) for e in node.contents]
        }

    def visit_LenStmt(self, node, offset=0):
        return {
            'type': 'LenStmt',
            'list': self.visit(node.contained_list)
        }

    def visit_AppendStmt(self, node, offset=0):
        return {
            'type': 'AppendStmt',
            'list': self.visit(node.list1),
            'value': self.visit(node.value)
        }

    def visit_PopStmt(self, node, offset=0):
        return {
            'type': 'PopStmt',
            'list': self.visit(node.contained_list),
            'index': self.visit(node.index)
        }

    def visit_RemoveStmt(self, node, offset=0):
        return {
            'type': 'RemoveStmt',
            'list': self.visit(node.contained_list),
            'value': self.visit(node.value)
        }

    def visit_ForStmt(self, node, offset=0):
        return {
            'type': 'ForStmt',
            'var': node.var,
            'a1': self.visit(node.a1) if isinstance(node.a1, Node) else node.a1,
            'a2': self.visit(node.a2) if isinstance(node.a2, Node) else node.a2,
            'a3': self.visit(node.a3) if isinstance(node.a3, Node) else node.a3,
            'body': [self.visit(s) for s in node.body]
        }

    def visit_NoneNode(self, node, offset=0):
        return {'type': 'None'}
