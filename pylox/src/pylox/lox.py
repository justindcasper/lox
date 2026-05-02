import argparse
import os
import sys

from . import AstPrinter
from . import Interpreter
from . import Parser
from . import RuntimeError
from . import Scanner
from . import Token
from . import TokenType

class Lox:
    def __init__(self):
        self.interpreter: Interpreter = Interpreter(self.runtime_error)
        self.had_error = False
        self.had_runtime_error = False

    def main(self, args: list[str]):
        parser = argparse.ArgumentParser(prog='pylox', description='Python implementation of the Lox language')
        parser.add_argument('script', nargs='?', default='')
        lox_args = parser.parse_args(args)

        if len(lox_args.script) > 0:
            self.run_file(lox_args.script)
        else:
            self.run_prompt()

    def run_file(self, path: str):
        with open(path, 'rb') as f:
            data = f.read()
            self.run(data.decode('utf-8'))
        
        # Indicate an error on exit
        if self.had_error:
            sys.exit(os.EX_DATAERR)
        if self.had_runtime_error:
            sys.exit(os.EX_SOFTWARE)
    
    def run_prompt(self):
        while True:
            try:
                line = input("> ")
                self.run(line, repl=True)
                self.had_error = False
                self.had_runtime_error = False
            except EOFError:
                break

    def run(self, source: str, repl=False):
        scanner = Scanner(source, self.error)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens, self.error)
        parsed = parser.parse_repl() if repl else parser.parse()

        # Stop if there was a syntax error
        if self.had_error:
            return
        
        if isinstance(parsed, list):
            self.interpreter.interpret(parsed)
        else:
            print(Interpreter.stringify(self.interpreter.interpret_expr(parsed)))

    def error(self, context: int | Token, message: str, *args, **kwargs):
        if type(context) is int:
            self.report(context, '', message)
        elif type(context) is Token:
            if context.type == TokenType.EOF:
                self.report(context.line, ' at end', message)
            else:
                self.report(context.line, f" at '{context.lexeme}'", message)

    def runtime_error(self, error: RuntimeError):
        print(f"{error}\n[line {error.token.line}]")
        self.had_runtime_error = True

    def report(self, line: int, where: str, message: str):
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        self.had_error = True
