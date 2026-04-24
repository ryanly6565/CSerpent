# Note: A large chunk of this code was taken from tutorial code

import ply.lex as lex

# -------------------------------
# Token list
# -------------------------------
tokens = (
    'NUMBER', 'IDENTIFIER',
    'PLUS','MINUS','TIMES','DIVIDE','ASSIGN',
    'LPAREN','RPAREN','LBRACKET','RBRACKET',
    'INDENT','DEDENT','NEWLINE','DOT','COMMA','COLON',
    'LT','GT','LE','GE','EQ','NE',
    'IF','ELIF','ELSE','FOR','IN','RANGE',
    'TRUE','FALSE','OR','AND','NOT',
    'DEF','RETURN','NONE','PRINT',
    'APPEND','POP','REMOVE','LEN'
)

# -------------------------------
# Reserved Words
# -------------------------------
reserved = {
    'if': 'IF','elif':'ELIF','else':'ELSE',
    'for':'FOR','in':'IN','range':'RANGE',
    'True':'TRUE','False':'FALSE','or':'OR',
    'and':'AND','not':'NOT','def':'DEF',
    'return':'RETURN','None':'NONE','print':'PRINT',
    'append':'APPEND','pop':'POP','remove':'REMOVE',
    'len':'LEN'
}

# -------------------------------
# Simple token regex rules
# -------------------------------
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'//'
t_ASSIGN  = r'='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACKET= r'\['
t_RBRACKET= r'\]'
t_COLON   = r':'
t_DOT     = r'\.'
t_LT      = r'<'
t_GT      = r'>'
t_LE      = r'<='
t_GE      = r'>='
t_EQ      = r'=='
t_NE      = r'!='
t_COMMA   = r','

# -------------------------------
# Tokens with functions
# -------------------------------
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    t.lexer.at_line_start = False
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value,'IDENTIFIER')
    t.lexer.at_line_start = False
    return t

def t_COMMENT(t):
    r'\#.*'
    t.lexer.at_line_start = False
    pass

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.at_line_start = True

    # Check for dedents on next line
    next_char = t.lexer.lexdata[t.lexer.lexpos: t.lexer.lexpos + 1]
    if next_char not in ('', ' ', '\t', '\n'):
        dedent_tokens = []
        # Create all dedents first
        while len(t.lexer.indent_stack) > 1:
            t.lexer.indent_stack.pop()
            tok = lex.LexToken()
            tok.type = 'DEDENT'
            tok.value = ''
            tok.lineno = t.lineno
            tok.lexpos = t.lexpos
            dedent_tokens.append(tok)

        # Add a newline at the very end (needed for parser grammer rules)
        if dedent_tokens:
            newline_token = lex.LexToken()
            newline_token.type = 'NEWLINE'
            newline_token.value = '\n'
            newline_token.lineno = t.lineno
            newline_token.lexpos = t.lexpos
            
            t.lexer.dedent_queue.extend(dedent_tokens)
            t.lexer.dedent_queue.append(newline_token)
            
            return t.lexer.dedent_queue.pop(0)

    # No dedents, just return newline
    newline_token = lex.LexToken()
    newline_token.type = 'NEWLINE'
    newline_token.value = '\n'
    newline_token.lineno = t.lineno
    newline_token.lexpos = t.lexpos
    return newline_token

# -------------------------------
# INDENT/DEDENT handling
# -------------------------------
def t_WHITESPACE(t):
    r'[ ]+'
    if not t.lexer.at_line_start:
        return None  # ignore spaces midline, these are not indents

    t.lexer.at_line_start = False
    spaces = len(t.value)
    prev = t.lexer.indent_stack[-1]

    if spaces == prev:
        return None  # same level, no INDENT/DEDENT

    elif spaces > prev:
        # Must be multiple of 4
        if (spaces - prev) % 4 != 0:
            raise IndentationError(f"Indent must be multiple of 4 (line {t.lineno})")
        t.lexer.indent_stack.append(spaces)
        t.type = 'INDENT'
        return t

    else:  # spaces < prev, dedent
        dedent_tokens = []
        while spaces < t.lexer.indent_stack[-1]:
            t.lexer.indent_stack.pop()
            tok = lex.LexToken()
            tok.type = 'DEDENT'
            tok.value = ''
            tok.lineno = t.lineno
            tok.lexpos = t.lexpos
            dedent_tokens.append(tok)

        if spaces != t.lexer.indent_stack[-1]:
            raise IndentationError(f"Invalid dedent at line {t.lineno}")

        # Queue dedent tokens and return the first
        t.lexer.dedent_queue.extend(dedent_tokens)
        return t.lexer.dedent_queue.pop(0)

# -------------------------------
# Error handling
# -------------------------------
def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

# -------------------------------
# Build lexer
# -------------------------------
lexer = lex.lex()
# initialize indent/dedent queues
lexer.indent_stack = [0]
lexer.at_line_start = True
lexer.dedent_queue = []

# Cite: This was done with the help of AI, as I couldn't figure out a way to do this just by myself
#       Michael said that he doesn't mind if we use AI. I essentially just prompted AI to help me figure out how to flush the tokens properly
# Wrap token() to handle queued DEDENTs and EOF
_original_token = lexer.token
def token_wrapper():
    # If we have queued DEDENTs, return them first
    if lexer.dedent_queue:
        return lexer.dedent_queue.pop(0)

    tok = _original_token()

    # At EOF, flush remaining indents
    if not tok:
        if len(lexer.indent_stack) > 1:
            while len(lexer.indent_stack) > 1:
                lexer.indent_stack.pop()
                eof_tok = lex.LexToken()
                eof_tok.type = 'DEDENT'
                eof_tok.value = ''
                eof_tok.lineno = lexer.lineno
                eof_tok.lexpos = lexer.lexpos
                lexer.dedent_queue.append(eof_tok)
            
            # Add NEWLINE after all DEDENTs at EOF
            newline_tok = lex.LexToken()
            newline_tok.type = 'NEWLINE'
            newline_tok.value = '\n'
            newline_tok.lineno = lexer.lineno
            newline_tok.lexpos = lexer.lexpos
            lexer.dedent_queue.append(newline_tok)

        # Return eof dedents/newline
        if lexer.dedent_queue:
            return lexer.dedent_queue.pop(0)
        return None

    return tok

lexer.token = token_wrapper