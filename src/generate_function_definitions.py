import os
import ast
import json

class FunctionExtractor(ast.NodeVisitor):
    def __init__(self):
        self.functions = []

    def visit_ClassDef(self, node):
        class_name = node.name.lower()
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name != "__init__":
                self._process_function(child, class_name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Skip standalone functions
        pass

    def visit_AsyncFunctionDef(self, node):
        # Skip standalone async functions
        pass

    def _process_function(self, node, class_name):
        docstring = ast.get_docstring(node, clean=True)
        if not docstring:
            return

        func_info = {
            "name": f"{class_name}__{node.name.lower()}",
            "description": docstring,
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "async": isinstance(node, ast.AsyncFunctionDef)
        }

        for arg in node.args.args:
            arg_name = arg.arg
            if arg_name == "self":
                continue

            arg_type = self._parse_annotation(arg.annotation) if arg.annotation else "string"

            func_info["parameters"]["properties"][arg_name] = {
                "type": arg_type
            }

            if not self._has_default_value(node, arg_name):
                func_info["parameters"]["required"].append(arg_name)

        self.functions.append(func_info)

    def _has_default_value(self, node, arg_name):
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        for arg, default in zip(node.args.args, defaults):
            if arg.arg == arg_name and default is not None:
                return True
        return False

    def _parse_annotation(self, annotation):
        """Parse type annotations to match OpenAI's types."""
        if isinstance(annotation, ast.Name):
            return self._map_type(annotation.id)
        elif isinstance(annotation, ast.Subscript):
            return "object"  # Simplified; advanced parsing can be added
        return "string"

    @staticmethod
    def _map_type(py_type):
        type_mapping = {
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }
        return type_mapping.get(py_type, "string")

def extract_functions_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        try:
            tree = ast.parse(file.read(), filename=filepath)
        except SyntaxError:
            return []

    extractor = FunctionExtractor()
    extractor.visit(tree)
    return extractor.functions

def scan_directories_for_functions(directories):
    all_functions = []

    for directory in directories:
        if not os.path.isdir(directory):
            print(f"Invalid directory path: {directory}")
            continue

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    functions = extract_functions_from_file(filepath)
                    all_functions.extend(functions)

    return all_functions

def main():
    directories = ["./aizen/data/news", "./aizen/social"]

    functions = scan_directories_for_functions(directories)

    output_file = "function_definitions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(functions, f, indent=4)

    print(f"Function definitions saved to {output_file}")

if __name__ == "__main__":
    main()
