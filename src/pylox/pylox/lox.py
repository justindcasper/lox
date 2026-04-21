import os
import sys
import typing

from . import Scanner

class Lox:
    def __init__(self):
        self.had_error = False

    def main(self, args: list[str]):
        if len(args) > 1:
            print("Usage: {pylox | lox} [script]")
            sys.exit(os.EX_USAGE)
        elif len(args) == 1:
            self.run_file(args[0])
        else:
            self.run_prompt()

    def run_file(self, path: str):
        with open(path, 'rb') as f:
            data = f.read()
            self.run(data.decode('utf-8'))
        
        # Indicate an error on exit
        if self.had_error:
            sys.exit(os.EX_DATAERR)
    
    def run_prompt(self):
        while True:
            try:
                line = input("> ")
                self.run(line)
                self.had_error = False
            except EOFError:
                break

    def run(self, source: str):
        scanner = Scanner(source, self.error)
        tokens = scanner.scan_tokens()

        for token in tokens:
            print(token)

    def error(self, line: int, message: str, *args, **kwargs):
        self.report(line, '', message)

    def report(self, line: int, where: str, message: str):
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        self.had_error = True
