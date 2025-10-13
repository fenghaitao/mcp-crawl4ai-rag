"""
DML Parser for Simics Device Modeling Language

This module provides parsing capabilities for Simics DML files to extract:
- Device definitions and inheritance
- Interface implementations 
- Method and attribute definitions
- Register definitions
- Event handling
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DMLDevice:
    """Represents a DML device definition"""
    name: str
    parent: Optional[str] = None
    file_path: str = ""
    line_number: int = 0
    interfaces: List[str] = None
    methods: List[str] = None
    attributes: List[str] = None
    registers: List[str] = None
    
    def __post_init__(self):
        if self.interfaces is None:
            self.interfaces = []
        if self.methods is None:
            self.methods = []
        if self.attributes is None:
            self.attributes = []
        if self.registers is None:
            self.registers = []


@dataclass
class DMLMethod:
    """Represents a DML method definition"""
    name: str
    device: str
    parameters: List[str]
    return_type: Optional[str] = None
    file_path: str = ""
    line_number: int = 0


@dataclass
class DMLAttribute:
    """Represents a DML attribute definition"""
    name: str
    device: str
    type_name: str
    file_path: str = ""
    line_number: int = 0


@dataclass
class DMLRegister:
    """Represents a DML register definition"""
    name: str
    device: str
    address: str
    size: Optional[str] = None
    file_path: str = ""
    line_number: int = 0


@dataclass
class DMLInterface:
    """Represents a DML interface definition"""
    name: str
    methods: List[str]
    file_path: str = ""
    line_number: int = 0
    
    def __post_init__(self):
        if self.methods is None:
            self.methods = []


class DMLParser:
    """Parser for Simics DML files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # DML syntax patterns
        self.patterns = {
            # Device definition: device uart_device : base_device { OR device NS16450;
            'device': re.compile(r'^\s*device\s+(\w+)\s*(?::\s*(\w+))?\s*[;{]', re.MULTILINE),
            
            # Interface definition: interface uart_interface {
            'interface': re.compile(r'^\s*interface\s+(\w+)\s*\{', re.MULTILINE),
            
            # Method definition: method read(addr) -> (value) {
            'method': re.compile(r'^\s*method\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*\(([^)]*)\))?\s*\{', re.MULTILINE),
            
            # Attribute definition: attribute clock_freq : uint64 = 100000000;
            'attribute': re.compile(r'^\s*attribute\s+(\w+)\s*:\s*(\w+)', re.MULTILINE),
            
            # Register definition: register control @ 0x00 size 4 {
            'register': re.compile(r'^\s*register\s+(\w+)\s*@\s*([x0-9a-fA-F]+)(?:\s+size\s+(\d+))?\s*\{?', re.MULTILINE),
            
            # Interface implementation: implement uart_interface;
            'implement': re.compile(r'^\s*implement\s+(\w+)\s*;', re.MULTILINE),
            
            # Import statement: import "base_device.dml";
            'import': re.compile(r'^\s*import\s+"([^"]+)"\s*;', re.MULTILINE),
            
            # Template usage: is template_name;
            'template': re.compile(r'^\s*is\s+(\w+)\s*;', re.MULTILINE),
        }
    
    def parse_dml_file(self, file_path: Path, base_path: Path = None) -> Dict[str, Any]:
        """
        Parse a DML file and extract structural information
        
        Args:
            file_path: Path to the DML file
            base_path: Base path for relative path calculation
            
        Returns:
            Dictionary containing extracted DML structure
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if base_path:
                relative_path = str(file_path.relative_to(base_path))
            else:
                relative_path = str(file_path)
            
            # Extract all structural elements
            devices = self._extract_devices(content, relative_path)
            interfaces = self._extract_interfaces(content, relative_path)
            methods = self._extract_methods(content, relative_path)
            attributes = self._extract_attributes(content, relative_path)
            registers = self._extract_registers(content, relative_path)
            imports = self._extract_imports(content)
            templates = self._extract_templates(content)
            
            # Link methods, attributes, registers to their devices
            self._link_elements_to_devices(devices, methods, attributes, registers, content)
            
            return {
                'file_path': relative_path,
                'file_type': 'dml',
                'devices': devices,
                'interfaces': interfaces,
                'methods': methods,
                'attributes': attributes,
                'registers': registers,
                'imports': imports,
                'templates': templates,
                'content_length': len(content),
                'line_count': content.count('\n') + 1,
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing DML file {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'file_type': 'dml',
                'error': str(e),
                'devices': [],
                'interfaces': [],
                'methods': [],
                'attributes': [],
                'registers': [],
                'imports': [],
                'templates': [],
            }
    
    def _extract_devices(self, content: str, file_path: str) -> List[DMLDevice]:
        """Extract device definitions from DML content"""
        devices = []
        
        for match in self.patterns['device'].finditer(content):
            device_name = match.group(1)
            parent_device = match.group(2) if match.group(2) else None
            line_number = content[:match.start()].count('\n') + 1
            
            # Find implemented interfaces for this device
            interfaces = self._find_device_interfaces(content, device_name, match.start())
            
            device = DMLDevice(
                name=device_name,
                parent=parent_device,
                file_path=file_path,
                line_number=line_number,
                interfaces=interfaces
            )
            devices.append(device)
            
        return devices
    
    def _extract_interfaces(self, content: str, file_path: str) -> List[DMLInterface]:
        """Extract interface definitions from DML content"""
        interfaces = []
        
        for match in self.patterns['interface'].finditer(content):
            interface_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            # Find methods in this interface (basic extraction)
            interface_methods = self._find_interface_methods(content, interface_name, match.start())
            
            interface = DMLInterface(
                name=interface_name,
                methods=interface_methods,
                file_path=file_path,
                line_number=line_number
            )
            interfaces.append(interface)
            
        return interfaces
    
    def _extract_methods(self, content: str, file_path: str) -> List[DMLMethod]:
        """Extract method definitions from DML content"""
        methods = []
        
        for match in self.patterns['method'].finditer(content):
            method_name = match.group(1)
            parameters_str = match.group(2) if match.group(2) else ""
            return_type = match.group(3) if match.group(3) else None
            line_number = content[:match.start()].count('\n') + 1
            
            # Parse parameters
            parameters = [p.strip() for p in parameters_str.split(',') if p.strip()]
            
            # Find which device this method belongs to
            device_name = self._find_containing_device(content, match.start())
            
            method = DMLMethod(
                name=method_name,
                device=device_name or "unknown",
                parameters=parameters,
                return_type=return_type,
                file_path=file_path,
                line_number=line_number
            )
            methods.append(method)
            
        return methods
    
    def _extract_attributes(self, content: str, file_path: str) -> List[DMLAttribute]:
        """Extract attribute definitions from DML content"""
        attributes = []
        
        for match in self.patterns['attribute'].finditer(content):
            attr_name = match.group(1)
            attr_type = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            
            # Find which device this attribute belongs to
            device_name = self._find_containing_device(content, match.start())
            
            attribute = DMLAttribute(
                name=attr_name,
                device=device_name or "unknown",
                type_name=attr_type,
                file_path=file_path,
                line_number=line_number
            )
            attributes.append(attribute)
            
        return attributes
    
    def _extract_registers(self, content: str, file_path: str) -> List[DMLRegister]:
        """Extract register definitions from DML content"""
        registers = []
        
        for match in self.patterns['register'].finditer(content):
            reg_name = match.group(1)
            reg_address = match.group(2)
            reg_size = match.group(3) if match.group(3) else None
            line_number = content[:match.start()].count('\n') + 1
            
            # Find which device this register belongs to
            device_name = self._find_containing_device(content, match.start())
            
            register = DMLRegister(
                name=reg_name,
                device=device_name or "unknown",
                address=reg_address,
                size=reg_size,
                file_path=file_path,
                line_number=line_number
            )
            registers.append(register)
            
        return registers
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from DML content"""
        imports = []
        
        for match in self.patterns['import'].finditer(content):
            import_path = match.group(1)
            imports.append(import_path)
            
        return imports
    
    def _extract_templates(self, content: str) -> List[str]:
        """Extract template usage from DML content"""
        templates = []
        
        for match in self.patterns['template'].finditer(content):
            template_name = match.group(1)
            templates.append(template_name)
            
        return templates
    
    def _find_device_interfaces(self, content: str, device_name: str, device_start: int) -> List[str]:
        """Find interfaces implemented by a specific device"""
        interfaces = []
        
        # Find the device block boundaries
        device_end = self._find_block_end(content, device_start)
        if device_end == -1:
            return interfaces
        
        device_block = content[device_start:device_end]
        
        # Find implement statements within this device block
        for match in self.patterns['implement'].finditer(device_block):
            interface_name = match.group(1)
            interfaces.append(interface_name)
            
        return interfaces
    
    def _find_interface_methods(self, content: str, interface_name: str, interface_start: int) -> List[str]:
        """Find methods defined in a specific interface"""
        methods = []
        
        # Find the interface block boundaries
        interface_end = self._find_block_end(content, interface_start)
        if interface_end == -1:
            return methods
        
        interface_block = content[interface_start:interface_end]
        
        # Find method definitions within this interface block
        for match in self.patterns['method'].finditer(interface_block):
            method_name = match.group(1)
            methods.append(method_name)
            
        return methods
    
    def _find_containing_device(self, content: str, position: int) -> Optional[str]:
        """Find which device contains the element at the given position"""
        # Look for all device declarations in the entire content
        device_matches = list(self.patterns['device'].finditer(content))
        
        if not device_matches:
            return None
        
        # Check if we have a single device declaration followed by semicolon
        # This means the entire file belongs to that device
        if len(device_matches) == 1:
            device_match = device_matches[0]
            device_name = device_match.group(1)
            
            # Check if it's a semicolon-terminated device declaration
            if content[device_match.end()-1] == ';':
                return device_name
        
        # Look backwards from position to find the nearest device declaration
        before_content = content[:position]
        device_matches_before = list(self.patterns['device'].finditer(before_content))
        
        if not device_matches_before:
            # If no device before this position, but we have devices in the file,
            # assume it belongs to the first device if it's semicolon-terminated
            if device_matches and content[device_matches[0].end()-1] == ';':
                return device_matches[0].group(1)
            return None
        
        # Get the last device declaration before this position
        last_device = device_matches_before[-1]
        device_name = last_device.group(1)
        device_start = last_device.start()
        
        # If it's a semicolon-terminated device, assume entire file belongs to it
        if content[last_device.end()-1] == ';':
            return device_name
        
        # Check if our position is within the device block (for brace-delimited devices)
        device_end = self._find_block_end(content, device_start)
        if device_end != -1 and position < device_end:
            return device_name
        
        return None
    
    def _find_block_end(self, content: str, start_pos: int) -> int:
        """Find the end of a block starting with { at start_pos"""
        # Find the opening brace
        brace_pos = content.find('{', start_pos)
        if brace_pos == -1:
            return -1
        
        # Count braces to find the matching closing brace
        brace_count = 0
        pos = brace_pos
        
        while pos < len(content):
            char = content[pos]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return pos + 1
            pos += 1
        
        return -1
    
    def _link_elements_to_devices(self, devices: List[DMLDevice], methods: List[DMLMethod], 
                                 attributes: List[DMLAttribute], registers: List[DMLRegister],
                                 content: str):
        """Link methods, attributes, and registers to their containing devices"""
        # Create a mapping of device names to device objects
        device_map = {device.name: device for device in devices}
        
        # Link methods to devices
        for method in methods:
            if method.device in device_map:
                device_map[method.device].methods.append(method.name)
        
        # Link attributes to devices
        for attribute in attributes:
            if attribute.device in device_map:
                device_map[attribute.device].attributes.append(attribute.name)
        
        # Link registers to devices
        for register in registers:
            if register.device in device_map:
                device_map[register.device].registers.append(register.name)


def main():
    """Test the DML parser"""
    parser = DMLParser()
    
    # Test with a sample DML file
    test_file = Path("test_device.dml")
    if test_file.exists():
        result = parser.parse_dml_file(test_file)
        print(f"Parsed {test_file}:")
        print(f"  Devices: {len(result['devices'])}")
        print(f"  Interfaces: {len(result['interfaces'])}")
        print(f"  Methods: {len(result['methods'])}")
        print(f"  Attributes: {len(result['attributes'])}")
        print(f"  Registers: {len(result['registers'])}")
    else:
        print("No test DML file found")


if __name__ == "__main__":
    main()