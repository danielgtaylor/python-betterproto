import re
from collections import defaultdict
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Dict,
    Iterator,
    List,
    Tuple,
)


@dataclass
class ModuleValidator:
    line_iterator: Iterator[str]
    line_number: int = field(init=False, default=0)

    collisions: Dict[str, List[Tuple[int, str]]] = field(
        init=False, default_factory=lambda: defaultdict(list)
    )

    def add_import(self, imp: str, number: int, full_line: str):
        """
        Adds an import to be tracked.
        """
        self.collisions[imp].append((number, full_line))

    def process_import(self, imp: str):
        """
        Filters out the import to its actual value.
        """
        if " as " in imp:
            imp = imp[imp.index(" as ") + 4 :]

        imp = imp.strip()
        assert " " not in imp, imp
        return imp

    def evaluate_multiline_import(self, line: str):
        """
        Evaluates a multiline import from a starting line
        """
        # Filter the first line and remove anything before the import statement.
        full_line = line
        line = line.split("import", 1)[1]
        if "(" in line:
            conditional = lambda line: ")" not in line
        else:
            conditional = lambda line: "\\" in line

        # Remove open parenthesis if it exists.
        if "(" in line:
            line = line[line.index("(") + 1 :]

        # Choose the conditional based on how multiline imports are formatted.
        while conditional(line):
            # Split the line by commas
            imports = line.split(",")

            for imp in imports:
                # Add the import to the namespace
                imp = self.process_import(imp)
                if imp:
                    self.add_import(imp, self.line_number, full_line)
            # Get the next line
            full_line = line = next(self.line_iterator)
            # Increment the line number
            self.line_number += 1

        # validate the last line
        if ")" in line:
            line = line[: line.index(")")]
        imports = line.split(",")
        for imp in imports:
            imp = self.process_import(imp)
            if imp:
                self.add_import(imp, self.line_number, full_line)

    def evaluate_import(self, line: str):
        """
        Extracts an import from a line.
        """
        whole_line = line
        line = line[line.index("import") + 6 :]
        values = line.split(",")
        for v in values:
            self.add_import(self.process_import(v), self.line_number, whole_line)

    def next(self):
        """
        Evaluate each line for names in the module.
        """
        line = next(self.line_iterator)

        # Skip lines with indentation or comments
        if (
            # Skip indents and whitespace.
            line.startswith(" ")
            or line == "\n"
            or line.startswith("\t")
            or
            # Skip comments
            line.startswith("#")
            or
            # Skip  decorators
            line.startswith("@")
        ):
            self.line_number += 1
            return

        # Skip docstrings.
        if line.startswith('"""') or line.startswith("'''"):
            quote = line[0] * 3
            line = line[3:]
            while quote not in line:
                line = next(self.line_iterator)
            self.line_number += 1
            return

        # Evaluate Imports.
        if line.startswith("from ") or line.startswith("import "):
            if "(" in line or "\\" in line:
                self.evaluate_multiline_import(line)
            else:
                self.evaluate_import(line)

        # Evaluate Classes.
        elif line.startswith("class "):
            class_name = re.search(r"class (\w+)", line).group(1)
            if class_name:
                self.add_import(class_name, self.line_number, line)

        # Evaluate Functions.
        elif line.startswith("def "):
            function_name = re.search(r"def (\w+)", line).group(1)
            if function_name:
                self.add_import(function_name, self.line_number, line)

        # Evaluate direct assignments.
        elif "=" in line:
            assignment = re.search(r"(\w+)\s*=", line).group(1)
            if assignment:
                self.add_import(assignment, self.line_number, line)

        self.line_number += 1

    def validate(self) -> bool:
        """
        Run Validation.
        """
        try:
            while True:
                self.next()
        except StopIteration:
            pass

        # Filter collisions for those with more than one value.
        self.collisions = {k: v for k, v in self.collisions.items() if len(v) > 1}

        # Return True if no collisions are found.
        return not bool(self.collisions)
