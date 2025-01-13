import os
import ast
import json
import re
from textwrap import dedent

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
        # Skip top-level/standalone functions (if you only want class methods)
        pass

    def visit_AsyncFunctionDef(self, node):
        # Skip standalone async functions (if you only want class methods)
        pass

    def _process_function(self, node, class_name):
        """
        Extract docstring, parse it, and build a JSON schema for OpenAI function calling.
        """
        raw_docstring = ast.get_docstring(node, clean=True)
        if not raw_docstring:
            # If there's no docstring, we skip
            return

        # 1. Parse docstring (split into description vs. arguments)
        parsed_doc = self._parse_docstring(raw_docstring)
        # parsed_doc will look like:
        # {
        #   "description": "... all lines above Args: ...",
        #   "args": {
        #       "arg_name": {
        #           "type": "string" or "number" or "boolean" etc,
        #           "description": "Arg description"
        #       },
        #       ...
        #   },
        #   "returns": "... everything in Returns block or you can omit"
        # }

        func_info = {
            "name": f"{class_name}__{node.name.lower()}",
            "description": parsed_doc["description"] + '\n\nReturns: ' + parsed_doc['returns'],   # without the 'Args:' section
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "async": isinstance(node, ast.AsyncFunctionDef)
        }

        # 2. For each formal argument in the function signature, update the schema
        for arg in node.args.args:
            arg_name = arg.arg
            # skip "self"
            if arg_name == "self":
                continue

            # Determine the OpenAI type from the annotation
            arg_type = self._parse_annotation(arg.annotation) if arg.annotation else "string"

            # Start the property schema for this arg
            func_info["parameters"]["properties"][arg_name] = {
                "type": arg_type,
            }

            # If docstring has a sub-description for this arg, add it
            # (fallback to an empty string if not present)
            doc_arg_info = parsed_doc["args"].get(arg_name, {})
            if doc_arg_info.get("description"):
                func_info["parameters"]["properties"][arg_name]["description"] = doc_arg_info["description"]

            # If the docstring provides a type override (e.g. doc says it's a float)
            # you can combine that logic or override the annotation-based type here
            # e.g. arg_type = doc_arg_info.get("type") or annotation-based

            # Determine if the argument has a default value
            if not self._has_default_value(node, arg_name):
                func_info["parameters"]["required"].append(arg_name)

        self.functions.append(func_info)

    def _has_default_value(self, node, arg_name):
        """
        Check whether a given argument has a default value.
        """
        # node.args.defaults is a list of the default values for the last len(defaults) arguments.
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        for arg, default in zip(node.args.args, defaults):
            if arg.arg == arg_name and default is not None:
                return True
        return False

    def _parse_annotation(self, annotation):
        """
        Convert Python type annotation AST to an OpenAI function calling type.
        """
        if isinstance(annotation, ast.Name):
            return self._map_type(annotation.id)
        elif isinstance(annotation, ast.Subscript):
            # For more sophisticated parsing, you could look at annotation.value/id
            # E.g. "List[str]" => "array of strings" or something similar
            return "array"
        return "string"

    @staticmethod
    def _map_type(py_type):
        """
        Maps Python built-in type names to OpenAI JSON schema types.
        """
        type_mapping = {
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }
        return type_mapping.get(py_type, "string")

    def _parse_docstring(self, docstring):
        """
        A basic parser for Google-style docstrings or similar:
        
            Short description.

            Longer description ...

            Args:
                param1 (int): explanation
                param2 (str): explanation

            Returns:
                Some text ...
        
        Returns a dict with:
          {
            "description": <str without Args block>,
            "args": {
                "param1": {
                    "type": <parsed from docstring if desired>,
                    "description": <description from docstring>
                },
                ...
            },
            "returns": <whatever was after Returns: if you want to capture it>
          }
        """
        # Dedent so we don’t misread leading spaces
        docstring = dedent(docstring)

        # Separate out the "Args:" block (and optionally "Returns:")
        # A simple approach is splitting by some known tokens
        args_block_pattern = r'(\n|^)Args:\s*'
        returns_block_pattern = r'(\n|^)Returns:\s*'

        # If you want to capture “Returns: …” to remove or keep, you can do so similarly
        # For simplicity, let's show an example capturing the Returns block in a group
        # (but you can do something else if needed).
        returns_match = re.search(returns_block_pattern + r'(.*)', docstring, flags=re.DOTALL)
        returns_text = ""
        if returns_match:
            returns_text = returns_match.group(2).strip()  # everything after 'Returns:'
            # remove that from the docstring
            docstring = re.sub(returns_block_pattern + r'(.*)', '', docstring, flags=re.DOTALL)

        # Now handle "Args:"
        args_match = re.search(args_block_pattern + r'(.*)', docstring, flags=re.DOTALL)
        args_text = ""
        if args_match:
            args_text = args_match.group(2).strip()  # everything after 'Args:' 
            # remove it from the docstring
            docstring = re.sub(args_block_pattern + r'(.*)', '', docstring, flags=re.DOTALL)

        # The remainder is the high-level description
        description = docstring.strip()

        # Now parse each line from args_text:
        # Typically each argument doc line is of form:
        #    param_name (type): description ...
        # We can parse them with a simple regex or line-splitting
        arg_info = {}
        arg_lines = args_text.splitlines()
        arg_line_pattern = re.compile(r'^\s*([\w_]+)\s*\(([^)]+)\):\s*(.*)')

        current_param = None
        for line in arg_lines:
            line = line.strip()
            if not line:
                continue

            m = arg_line_pattern.match(line)
            if m:
                # Found a new argument line
                param_name, param_type, param_desc = m.groups()
                arg_info[param_name] = {
                    "type": FunctionExtractor._map_type(param_type.strip()),
                    "description": param_desc.strip()
                }
                current_param = param_name
            else:
                # If the line doesn’t match the pattern, it might be a continuation
                # of the previous param’s description. Append if needed.
                if current_param and line:
                    arg_info[current_param]["description"] += f" {line}"

        return {
            "description": description,
            "args": arg_info,
            "returns": returns_text
        }

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
    directories = ["./aizen/data/news", "./aizen/social", "./aizen/chains"]

    functions = scan_directories_for_functions(directories)

    output_file = "function_definitions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(functions, f, indent=4)

    print(f"Function definitions saved to {output_file}")

if __name__ == "__main__":
    main()
