"""
Simics Test Analyzer for Python test files

This module extends the existing Python AST analysis to add Simics-specific
patterns for test files, including:
- Simics API usage detection
- Device instantiation patterns
- Test fixture analysis
- Test validation patterns
"""

import ast
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from parse_repo_into_neo4j import Neo4jCodeAnalyzer


@dataclass
class SimicsAPICall:
    """Represents a Simics API call in test code"""
    api_name: str
    module: str
    function: str
    line_number: int
    context: str = ""


@dataclass
class DeviceInstantiation:
    """Represents device creation/instantiation in tests"""
    device_name: str
    device_type: str
    line_number: int
    test_function: str = ""


@dataclass
class TestFunction:
    """Represents a test function with Simics-specific metadata"""
    name: str
    class_name: Optional[str]
    line_number: int
    devices_tested: List[str]
    simics_apis_used: List[str]
    fixtures_used: List[str]
    assertions: List[str]


@dataclass
class TestFixture:
    """Represents a pytest fixture"""
    name: str
    scope: str
    line_number: int
    dependencies: List[str]


class SimicsTestAnalyzer(Neo4jCodeAnalyzer):
    """Enhanced analyzer for Simics Python test files"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Simics-specific patterns
        self.simics_modules = {
            'simics', 'pyobj', 'cli', 'SIM_', 'conf', 'simbricks'
        }
        
        # Common Simics API patterns
        self.simics_api_patterns = {
            'device_creation': re.compile(r'(?:SIM_|conf\.|simics\.)create_object|new_.*_device'),
            'simulation_control': re.compile(r'(?:SIM_|simics\.)(?:run|stop|step|continue)'),
            'memory_operations': re.compile(r'(?:SIM_|simics\.)(?:read|write)_(?:phys_)?memory'),
            'register_access': re.compile(r'(?:SIM_|simics\.)(?:read|write)_register'),
            'attribute_access': re.compile(r'(?:SIM_|simics\.)(?:get|set)_attribute'),
        }
        
        # Test patterns
        self.test_patterns = {
            'test_function': re.compile(r'^test_'),
            'fixture_function': re.compile(r'@pytest\.fixture'),
            'assertion': re.compile(r'assert\s+'),
        }
    
    def analyze_test_file(self, file_path: Path, repo_root: Path = None, 
                         project_modules: Set[str] = None) -> Dict[str, Any]:
        """
        Analyze a Python test file with Simics-specific enhancements
        
        Args:
            file_path: Path to the test file
            repo_root: Root path of the repository
            project_modules: Set of project module names
            
        Returns:
            Dictionary containing enhanced test analysis
        """
        try:
            # Ensure project_modules is not None
            if project_modules is None:
                project_modules = set()
            
            # Get base Python analysis
            base_analysis = self.analyze_python_file(file_path, repo_root, project_modules)
            
            # Handle case where base analysis fails
            if base_analysis is None:
                base_analysis = {
                    'file_path': str(file_path.relative_to(repo_root)) if repo_root else str(file_path),
                    'module_name': file_path.stem,
                    'classes': [],
                    'functions': [],
                    'imports': [],
                    'line_count': 0
                }
            
            # Add Simics-specific analysis
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract Simics-specific patterns
            simics_analysis = {
                'simics_imports': self._extract_simics_imports(tree),
                'simics_api_calls': self._extract_simics_api_calls(tree, content),
                'device_instantiations': self._extract_device_instantiations(tree, content),
                'test_functions': self._extract_test_functions(tree, content),
                'test_fixtures': self._extract_test_fixtures(tree, content),
                'test_assertions': self._extract_test_assertions(tree, content),
                'devices_under_test': self._extract_devices_under_test(tree, content),
                'test_categories': self._categorize_tests(tree, content),
            }
            
            # Merge base analysis with Simics analysis
            enhanced_analysis = {**base_analysis, **simics_analysis}
            enhanced_analysis['file_type'] = 'test'
            enhanced_analysis['is_simics_test'] = len(simics_analysis['simics_imports']) > 0
            
            return enhanced_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing test file {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'file_type': 'test',
                'error': str(e),
                'simics_imports': [],
                'simics_api_calls': [],
                'device_instantiations': [],
                'test_functions': [],
                'test_fixtures': [],
            }
    
    def _extract_simics_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract Simics-related import statements"""
        simics_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(simics_mod in alias.name for simics_mod in self.simics_modules):
                        simics_imports.append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'line_number': node.lineno,
                            'type': 'import'
                        })
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and any(simics_mod in node.module for simics_mod in self.simics_modules):
                    for alias in node.names:
                        simics_imports.append({
                            'module': node.module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line_number': node.lineno,
                            'type': 'from_import'
                        })
        
        return simics_imports
    
    def _extract_simics_api_calls(self, tree: ast.AST, content: str) -> List[SimicsAPICall]:
        """Extract Simics API calls from the code"""
        api_calls = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Extract function call information
                call_info = self._analyze_function_call(node)
                
                if call_info and self._is_simics_api_call(call_info):
                    context = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                    
                    api_call = SimicsAPICall(
                        api_name=call_info['full_name'],
                        module=call_info['module'],
                        function=call_info['function'],
                        line_number=node.lineno,
                        context=context
                    )
                    api_calls.append(api_call)
        
        return api_calls
    
    def _extract_device_instantiations(self, tree: ast.AST, content: str) -> List[DeviceInstantiation]:
        """Extract device creation/instantiation patterns"""
        devices = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_info = self._analyze_function_call(node)
                
                if call_info and self._is_device_creation_call(call_info):
                    # Try to extract device name and type from arguments
                    device_info = self._extract_device_info_from_call(node, lines)
                    
                    if device_info:
                        # Find containing test function
                        test_function = self._find_containing_function(tree, node.lineno)
                        
                        device = DeviceInstantiation(
                            device_name=device_info['name'],
                            device_type=device_info['type'],
                            line_number=node.lineno,
                            test_function=test_function or ""
                        )
                        devices.append(device)
        
        return devices
    
    def _extract_test_functions(self, tree: ast.AST, content: str) -> List[TestFunction]:
        """Extract test function definitions with metadata"""
        test_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                # Find class context if any
                class_name = self._find_containing_class(tree, node.lineno)
                
                # Analyze test function content
                test_analysis = self._analyze_test_function_content(node, content)
                
                test_func = TestFunction(
                    name=node.name,
                    class_name=class_name,
                    line_number=node.lineno,
                    devices_tested=test_analysis['devices_tested'],
                    simics_apis_used=test_analysis['simics_apis_used'],
                    fixtures_used=test_analysis['fixtures_used'],
                    assertions=test_analysis['assertions']
                )
                test_functions.append(test_func)
        
        return test_functions
    
    def _extract_test_fixtures(self, tree: ast.AST, content: str) -> List[TestFixture]:
        """Extract pytest fixture definitions"""
        fixtures = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has pytest.fixture decorator
                fixture_info = self._extract_fixture_info(node)
                
                if fixture_info:
                    fixture = TestFixture(
                        name=node.name,
                        scope=fixture_info['scope'],
                        line_number=node.lineno,
                        dependencies=fixture_info['dependencies']
                    )
                    fixtures.append(fixture)
        
        return fixtures
    
    def _extract_test_assertions(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Extract assertion statements from tests"""
        assertions = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                # Get the assertion text
                line_text = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                
                # Analyze assertion type
                assertion_type = self._categorize_assertion(node)
                
                assertions.append({
                    'line_number': node.lineno,
                    'text': line_text,
                    'type': assertion_type,
                    'test_function': self._find_containing_function(tree, node.lineno)
                })
        
        return assertions
    
    def _extract_devices_under_test(self, tree: ast.AST, content: str) -> List[str]:
        """Extract names of devices being tested"""
        devices = set()
        
        # Look for device creation calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_info = self._analyze_function_call(node)
                
                if call_info and self._is_device_creation_call(call_info):
                    device_info = self._extract_device_info_from_call(node, content.split('\n'))
                    if device_info:
                        devices.add(device_info['type'])
        
        # Look for device names in comments and strings
        device_patterns = re.findall(r'(?:test|device|mock).*?(\w+_device|\w+_controller)', content, re.IGNORECASE)
        devices.update(device_patterns)
        
        return list(devices)
    
    def _categorize_tests(self, tree: ast.AST, content: str) -> List[str]:
        """Categorize the types of tests in this file"""
        categories = set()
        
        # Analyze test function names and content for categories
        test_patterns = {
            'unit': ['unit', 'mock', 'stub'],
            'integration': ['integration', 'end_to_end', 'e2e'],
            'performance': ['performance', 'benchmark', 'speed', 'timing'],
            'regression': ['regression', 'bug', 'issue'],
            'device': ['device', 'hardware', 'register', 'memory'],
            'api': ['api', 'interface', 'protocol'],
        }
        
        content_lower = content.lower()
        
        for category, keywords in test_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.add(category)
        
        return list(categories)
    
    # Helper methods
    
    def _analyze_function_call(self, node: ast.Call) -> Optional[Dict[str, str]]:
        """Analyze a function call node to extract module and function info"""
        if isinstance(node.func, ast.Name):
            return {
                'full_name': node.func.id,
                'module': '',
                'function': node.func.id
            }
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return {
                    'full_name': f"{node.func.value.id}.{node.func.attr}",
                    'module': node.func.value.id,
                    'function': node.func.attr
                }
        return None
    
    def _is_simics_api_call(self, call_info: Dict[str, str]) -> bool:
        """Check if a function call is a Simics API call"""
        full_name = call_info['full_name']
        module = call_info['module']
        
        # Check module names
        if any(simics_mod in module for simics_mod in self.simics_modules):
            return True
        
        # Check function patterns
        if any(pattern.search(full_name) for pattern in self.simics_api_patterns.values()):
            return True
        
        return False
    
    def _is_device_creation_call(self, call_info: Dict[str, str]) -> bool:
        """Check if a function call creates a device"""
        patterns = ['create_object', 'new_', '_device', '_controller', 'instantiate']
        full_name = call_info['full_name'].lower()
        
        return any(pattern in full_name for pattern in patterns)
    
    def _extract_device_info_from_call(self, node: ast.Call, lines: List[str]) -> Optional[Dict[str, str]]:
        """Extract device name and type from a device creation call"""
        # This is a simplified extraction - could be enhanced based on actual Simics patterns
        try:
            # Look for string arguments that might be device names/types
            for arg in node.args:
                if isinstance(arg, ast.Str):
                    value = arg.s
                    if 'device' in value.lower() or 'controller' in value.lower():
                        return {
                            'name': value,
                            'type': value
                        }
            
            # Fallback: try to extract from line context
            line_text = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            device_match = re.search(r'(\w*device\w*|\w*controller\w*)', line_text, re.IGNORECASE)
            if device_match:
                device_name = device_match.group(1)
                return {
                    'name': device_name,
                    'type': device_name
                }
        except:
            pass
        
        return None
    
    def _find_containing_function(self, tree: ast.AST, line_number: int) -> Optional[str]:
        """Find the function that contains the given line number"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if line is within this function
                if hasattr(node, 'end_lineno') and node.lineno <= line_number <= node.end_lineno:
                    return node.name
                # Fallback for older Python versions
                elif node.lineno <= line_number:
                    # This is a rough approximation
                    return node.name
        return None
    
    def _find_containing_class(self, tree: ast.AST, line_number: int) -> Optional[str]:
        """Find the class that contains the given line number"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if hasattr(node, 'end_lineno') and node.lineno <= line_number <= node.end_lineno:
                    return node.name
                elif node.lineno <= line_number:
                    return node.name
        return None
    
    def _analyze_test_function_content(self, func_node: ast.FunctionDef, content: str) -> Dict[str, List[str]]:
        """Analyze the content of a test function"""
        analysis = {
            'devices_tested': [],
            'simics_apis_used': [],
            'fixtures_used': [],
            'assertions': []
        }
        
        # Extract fixture usage from function parameters
        for arg in func_node.args.args:
            if arg.arg != 'self':  # Skip self parameter
                analysis['fixtures_used'].append(arg.arg)
        
        # Analyze function body
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_info = self._analyze_function_call(node)
                if call_info and self._is_simics_api_call(call_info):
                    analysis['simics_apis_used'].append(call_info['full_name'])
                
                if call_info and self._is_device_creation_call(call_info):
                    device_info = self._extract_device_info_from_call(node, content.split('\n'))
                    if device_info:
                        analysis['devices_tested'].append(device_info['type'])
            
            elif isinstance(node, ast.Assert):
                # Extract assertion information
                analysis['assertions'].append(f"line_{node.lineno}")
        
        return analysis
    
    def _extract_fixture_info(self, func_node: ast.FunctionDef) -> Optional[Dict[str, Any]]:
        """Extract pytest fixture information from function decorators"""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'fixture':
                    # Extract fixture scope and other parameters
                    scope = 'function'  # default
                    dependencies = []
                    
                    for keyword in decorator.keywords:
                        if keyword.arg == 'scope' and isinstance(keyword.value, ast.Str):
                            scope = keyword.value.s
                    
                    # Extract dependencies from function parameters
                    for arg in func_node.args.args:
                        dependencies.append(arg.arg)
                    
                    return {
                        'scope': scope,
                        'dependencies': dependencies
                    }
            
            elif isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture':
                return {
                    'scope': 'function',
                    'dependencies': [arg.arg for arg in func_node.args.args]
                }
        
        return None
    
    def _categorize_assertion(self, assert_node: ast.Assert) -> str:
        """Categorize the type of assertion"""
        # Analyze the assertion expression to categorize it
        test_expr = assert_node.test
        
        if isinstance(test_expr, ast.Compare):
            return 'comparison'
        elif isinstance(test_expr, ast.Call):
            return 'function_call'
        elif isinstance(test_expr, ast.BoolOp):
            return 'boolean_logic'
        else:
            return 'simple'


def main():
    """Test the Simics test analyzer"""
    analyzer = SimicsTestAnalyzer()
    
    # Test with sample files if they exist
    test_files = [
        "test_device.py",
        "test_uart.py", 
        "device_test.py"
    ]
    
    for test_file in test_files:
        test_path = Path(test_file)
        if test_path.exists():
            result = analyzer.analyze_test_file(test_path)
            print(f"\nAnalyzed {test_file}:")
            print(f"  Simics imports: {len(result['simics_imports'])}")
            print(f"  API calls: {len(result['simics_api_calls'])}")
            print(f"  Device instantiations: {len(result['device_instantiations'])}")
            print(f"  Test functions: {len(result['test_functions'])}")
            print(f"  Test fixtures: {len(result['test_fixtures'])}")
            print(f"  Is Simics test: {result['is_simics_test']}")


if __name__ == "__main__":
    main()