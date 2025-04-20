import ast

def check_syntax(filename):
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            source = file.read()
        ast.parse(source)
        print(f'No syntax errors detected in {filename}')
        return True
    except SyntaxError as e:
        print(f'Syntax error in {filename} at line {e.lineno}, column {e.offset}: {e.msg}')
        return False

check_syntax('main.py') 