import json
from typing import Dict, List, Optional

class FunctionRegistry:
    """Registry to manage and validate function definitions"""
    
    def __init__(self, function_definitions: List[Dict]):
        self.functions = {}
        self.class_functions = {}
        
        # Parse function definitions
        for func in function_definitions:
            name = func['name']
            class_name = name.split('__')[0] if '__' in name else None
            
            if class_name:
                if class_name not in self.class_functions:
                    self.class_functions[class_name] = {}
                self.class_functions[class_name][name] = func
            
            self.functions[name] = func

    def get_function_def(self, name: str) -> Optional[Dict]:
        """Get function definition by name"""
        return self.functions.get(name)

    def get_class_functions(self, class_name: str) -> Dict:
        """Get all functions for a specific class"""
        return self.class_functions.get(class_name, {})

    def validate_function(self, name: str) -> bool:
        """Check if function exists in registry"""
        return name in self.functions

    def get_openai_tool_definition(self, name: str) -> Dict:
        """Convert function definition to OpenAI tool format"""
        func_def = self.get_function_def(name)
        if not func_def:
            raise ValueError(f"Function {name} not found in registry")
            
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": func_def.get('description', ''),
                "parameters": func_def.get('parameters', {})
            }
        }

    @classmethod
    def load_from_json(cls, json_path: str) -> 'FunctionRegistry':
        """Load function definitions from JSON file"""
        with open(json_path, 'r') as f:
            definitions = json.load(f)
        return cls(definitions)