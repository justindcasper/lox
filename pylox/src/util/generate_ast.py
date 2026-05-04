import argparse
import os
import typing

INDENT = ' ' * 4

def main():
    parser = argparse.ArgumentParser(prog='generate_ast', description='Generate Abstract Syntax Trees')
    parser.add_argument('output_directory')
    args = parser.parse_args()

    output_dir = args.output_directory
    define_ast(output_dir, 'Expr', [
        'Assign   : Token name, Expr value',
        'Ternary  : Expr condition, Token question, Expr then_expr, Token colon, Expr else_expr',
        'Binary   : Expr left, Token operator, Expr right',
        'Call     : Expr callee, Token paren, list[Expr] arguments',
        'Grouping : Expr expression',
        'Literal  : object value',
        'Logical  : Expr left, Token operator, Expr right',
        'Unary    : Token operator, Expr right',
        'Variable : Token name'
    ], needs_importing=['Token'])

    define_ast(output_dir, 'Stmt', [
        'Block          : list[Stmt] statements',
        'BreakStmt      : Token keyword',
        'ExpressionStmt : Expr expression',
        'FunctionStmt   : Token name, list[Token] params, list[Stmt] body',
        'IfStmt         : Expr condition, Stmt then_branch, Stmt else_branch',
        'PrintStmt      : Expr expression',
        'ReturnStmt     : Token keyword, Expr value',
        'VarStmt        : Token name, Expr initializer',
        'WhileStmt      : Expr condition, Stmt body'
    ], needs_importing=['Expr', 'Token'])
    
def define_ast(output_dir: str, base_name: str, types: list[str], needs_importing: list[str] = []) -> None:
    path = os.path.join(output_dir, base_name + '.py')
    with open(path, 'w') as output:
        print(f'from abc import ABC, abstractmethod', file=output)
        print('', file=output)
        for ni in needs_importing:
            print(f'from pylox import {ni}', file=output)
        print('', file=output)
        print(f'class {base_name}(ABC):', file=output)
        print(f'{INDENT}@abstractmethod', file=output)
        print(f'{INDENT}def accept(visitor: "{base_name}Visitor"):', file=output)
        print(f'{INDENT}{INDENT}pass', file=output)
        print('', file=output)

        define_visitor(output, base_name, types)

        # The AST classes
        for type in types:
            class_name = type.split(':')[0].strip()
            fields = type.split(':')[1].strip()
            define_type(output, base_name, class_name, fields)

def define_visitor(output: typing.TextIO, base_name: str, types: list[str]) -> None:
    print(f'class {base_name}Visitor(ABC):', file=output)
    lower_base_name = base_name.lower()

    for type in types:
        type_name = type.split(':')[0].strip()
        lower_type_name = type_name.lower()
        print(f'{INDENT}@abstractmethod', file=output)
        print(f'{INDENT}def visit_{lower_type_name}_{lower_base_name}(self, {lower_type_name}: "{type_name}"):', file=output)
        print(f'{INDENT}{INDENT}pass', file=output)

    print('', file=output)

def define_type(output: typing.TextIO, base_name: str, class_name: str, field_list: str) -> None:
    print(f'class {class_name}({base_name}):', file=output)

    # Constructor
    pythonic_field_list = _turn_fields_pythonic(field_list)
    print(f'{INDENT}def __init__(self, {pythonic_field_list}):', file=output)

    # Store parameters in fields
    fields = field_list.split(',')
    for field in fields:
        type = field.split()[0].strip()
        name = field.split()[1].strip()
        print(f'{INDENT}{INDENT}self.{name}: {type} = {name}', file=output)

    print(f'{INDENT}', file=output)
    # Visitor pattern
    lower_class_name = class_name.lower()
    lower_base_name = base_name.lower()
    print(f'{INDENT}def accept(self, visitor: {base_name}Visitor):', file=output)
    print(f'{INDENT}{INDENT}return visitor.visit_{lower_class_name}_{lower_base_name}(self)', file=output)
    
    print('', file=output)

def _turn_fields_pythonic(fields: str):
    split_up_fields = [field.split() for field in fields.split(',')]
    type_second = [': '.join([field[1], field[0]]) for field in split_up_fields]
    pythonic = ', '.join(type_second)
    return pythonic


if __name__ == "__main__":
    main()
