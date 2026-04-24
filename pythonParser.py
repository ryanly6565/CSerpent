"""
PLY Parser (Taken from tutorial)
=========================================================

This parser handles:
- Variables and assignments
- Arithmetic expressions
- If/elif/else statements
- For loops
- Print statements
- Comments
- Lists and some related methods (len, append, remove, pop)
"""

import ply.yacc as yacc
import sys
import pythonLexer
from pythonAst import UnaryOp, BinOp, Constant, AssignStmt, IfStmt, Return, Parameter, Function, PrintStmt, List, LenStmt, AppendStmt, RemoveStmt, PopStmt, CallFunction, NoneNode, Program, ForStmt

tokens = pythonLexer.tokens
lexer = pythonLexer.lexer

# ==============================================================================
# PARSER - Grammar and Semantic Actions
# ==============================================================================

# Precedence and associativity
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'EQ', 'NE'),
    ('left', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
    ('left', 'DOT')
)

# ==============================================================================
# Grammar Rules
# ==============================================================================

# General program rules
def p_program(p):
    '''program : opt_newlines statement_list opt_newlines'''
    p[0] = Program(p[2])

def p_statement_list(p):
    '''statement_list : statement_list NEWLINE statement
                     | statement'''
    if len(p) == 4:
        left = p[1] or []
        stmt = p[3]
        if stmt is None:
            p[0] = left
        else:
            p[0] = left + [stmt]
    else:
        stmt = p[1]
        if stmt is None:
            p[0] = []
        else:
            p[0] = [stmt]

def p_optnewlines(p):
    '''opt_newlines : NEWLINE opt_newlines
                    | empty '''
    pass

def p_empty(p):
    '''empty : '''
    pass

def p_statement(p):
    '''statement : assignment_statement
                | if_statement
                | for_statement
                | print_statement
                | append_statement
                | remove_statement
                | function
                | expression'''
    if p[1] is None:
        p[0] = None
    else:
        p[0] = p[1]

def p_assignment_statement(p):
    '''assignment_statement : IDENTIFIER ASSIGN expression'''
    p[0] = AssignStmt(p[1], p[3])

def p_print_statement(p):
    '''print_statement : PRINT LPAREN expression RPAREN'''
    p[0] = PrintStmt(p[3])

# Expression rules
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression
                  | expression EQ expression
                  | expression NE expression
                  | expression AND expression
                  | expression OR expression'''
    p[0] = BinOp(p[2], p[1], p[3])

def p_expression_pop(p):
    '''expression : pop_statement '''
    p[0] = p[1]

def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = UnaryOp('-', p[2])

def p_expression_not(p):
    '''expression : NOT expression'''
    p[0] = UnaryOp('not', p[2])

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_number(p):
    '''expression : NUMBER'''
    p[0] = Constant('int', p[1])

def p_expression_identifier(p):
    '''expression : IDENTIFIER'''
    p[0] = Constant('id', p[1])

def p_expression_none(p):
    '''expression : NONE'''
    p[0] = NoneNode()

def p_expression_bool(p):
    '''expression : TRUE 
                | FALSE'''
    if p[1] == 'True':
        p[0] = Constant('bool', True)
    else:
        p[0] = Constant('bool', False)

def p_expression_list(p):
    '''expression : list'''
    p[0] = p[1]

def p_len_statement(p):
    '''expression : LEN LPAREN expression RPAREN'''
    p[0] = LenStmt(p[3])

# If statements
def p_if_statement(p):
    '''if_statement : IF LPAREN expression RPAREN COLON NEWLINE INDENT statement_list opt_newlines DEDENT NEWLINE elif_chain else_clause
                   | IF LPAREN expression RPAREN COLON NEWLINE INDENT statement_list opt_newlines DEDENT NEWLINE elif_chain
                   | IF LPAREN expression RPAREN COLON NEWLINE INDENT statement_list opt_newlines DEDENT NEWLINE else_clause
                   | IF LPAREN expression RPAREN COLON NEWLINE INDENT statement_list opt_newlines DEDENT'''
    condition = p[3]
    if_block = p[8]
    else_block = None
    
    # Determine what follows the if block
    if len(p) == 11:  # Just if, no elif or else
        else_block = None
    elif len(p) == 13:  # if + elif OR if + else
        else_block = p[12]
    elif len(p) == 14:  # if + elif + else
        elif_chain = p[12]
        else_clause = p[13]
        # Attach else to the end of the elif chain
        last_elif = elif_chain
        while last_elif.orelse is not None:
            last_elif = last_elif.orelse[0]
        last_elif.orelse = else_clause
        else_block = elif_chain
    
    p[0] = IfStmt(condition, if_block, else_block)

def p_elif_chain(p):
    '''elif_chain : elif_chain elif_statement
                  | elif_statement'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        # Chain elifs, need to attach the new elif to the end of the chain
        last_elif = p[1]
        while last_elif.orelse is not None:
            last_elif = last_elif.orelse[0]
        last_elif.orelse = [p[2]]
        p[0] = p[1]

def p_elif_statement(p):
    '''elif_statement : ELIF LPAREN expression RPAREN COLON NEWLINE INDENT statement_list opt_newlines DEDENT NEWLINE'''
    p[0] = IfStmt(p[3], p[8], None)

def p_else_clause(p):
    '''else_clause : ELSE COLON NEWLINE INDENT statement_list opt_newlines DEDENT NEWLINE'''
    p[0] = p[5]

def p_list_values(p):
    '''list_values : list_values COMMA expression
                    | expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_list(p):
    '''list : LBRACKET list_values RBRACKET
            | LBRACKET RBRACKET'''
    if len(p) == 3:
        p[0] = List([])
    else:
        p[0] = List(p[2])

def p_append_statement(p):
    '''append_statement : expression DOT APPEND LPAREN expression RPAREN'''
    p[0] = AppendStmt(p[1], p[5])

def p_remove_statement(p):
    '''remove_statement : expression DOT REMOVE LPAREN expression RPAREN'''
    p[0] = RemoveStmt(p[1], p[5])

def p_pop_statement(p):
    '''pop_statement : expression DOT POP LPAREN expression RPAREN'''
    p[0] = PopStmt(p[1], p[5])

# General function rules
def p_function(p):
    '''function : DEF IDENTIFIER LPAREN params RPAREN COLON NEWLINE INDENT statement_list opt_newlines return opt_newlines DEDENT'''
    p[0] = Function(p[2], p[4], p[9] + [p[11]])

def p_parameters(p):
    '''params : params COMMA IDENTIFIER
            | IDENTIFIER'''
    if len(p) == 2:
        p[0] = [Parameter(p[1])]
    else:
        p[0] = p[1] + [Parameter(p[3])]

def p_return(p):
    '''return : RETURN expression
              | RETURN'''
    if len(p) == 3:
        p[0] = Return(p[2])
    else:
        p[0] = Return(NoneNode())

def p_arguments(p):
    '''args : args COMMA expression
            | expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_expression_call_function(p):
    '''expression : IDENTIFIER LPAREN args RPAREN'''
    p[0] = CallFunction(p[1], p[3])

# For statement
def p_for_inputs(p):
    '''for_inputs : expression COMMA expression COMMA expression
                | expression COMMA expression
                | expression'''
    if len(p) == 6:
        p[0] = {'a1': p[1], 'a2': p[3], 'a3': p[5]}
    elif len(p) == 4:
        p[0] = {'a1': p[1], 'a2': p[3]}
    else:
        p[0] = {'a2': p[1]}

def p_for_statement(p):
    '''for_statement : FOR IDENTIFIER IN RANGE LPAREN for_inputs RPAREN COLON NEWLINE INDENT statement_list opt_newlines DEDENT'''
    a1 = p[6].get("a1")
    a2 = p[6].get("a2")
    a3 = p[6].get("a3")
    p[0] = ForStmt(p[2], a2, p[11], a1=a1, a3=a3)

def p_error(p):
    if not p:
        print("Syntax error at EOF")
        return
    
    tok = repr(p.value) if p.value else p.type
    sys.exit(f"Syntax error at token {tok} on line {p.lineno}")

    while True:
        tok = parser.token()
        if not tok or tok.type == "NEWLINE":
            break

    return tok

# Build parser
parser = yacc.yacc()