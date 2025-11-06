# tree-sitter-dml

A Tree-sitter grammar for DML (Device Modeling Language) 1.4, used in Intel Simics for hardware device modeling.

## Overview

This parser implements a comprehensive grammar for DML 1.4, covering:

- **Device structure**: devices, banks, registers, fields, ports, attributes, etc.
- **Templates**: reusable object patterns with inheritance
- **Methods**: regular, inline, independent, startup, memoized, and shared methods
- **Type system**: C-compatible types with DML extensions (struct, layout, bitfields, sequence, hook)
- **Expressions**: full operator support including compile-time conditionals
- **Statements**: control flow, loops, error handling, logging
- **Data declarations**: session, saved, and local variables
- **Conditional compilation**: `#if`, `#else`, `#foreach`, `#select`
- **Import/Export**: module system
- **Header/Footer blocks**: inline C code

## Features

### Language Support

- ✅ All DML 1.4 keywords and operators
- ✅ Device hierarchy (device → bank → register → field)
- ✅ Template system with multiple inheritance
- ✅ Method declarations with input/output parameters
- ✅ Compile-time and runtime conditionals
- ✅ Complete expression grammar with proper precedence
- ✅ All statement types (if, while, for, switch, try-catch, etc.)
- ✅ Type system (primitives, structs, layouts, bitfields, sequences, hooks)
- ✅ Initializers and designated initializers
- ✅ Comments (single-line and multi-line)

### Grammar Structure

The grammar follows the official DML 1.4 specification with:

- **Operator precedence**: 15 levels from postfix (160) to assignment (20)
- **Proper associativity**: Left for most operators, right for unary/conditional/assignment
- **Conflict resolution**: Strategic use of `prec` and `prec.left`/`prec.right`
- **Whitespace handling**: Flexible whitespace and comment support

## Installation

### Prerequisites

- Node.js (for running tree-sitter CLI)
- A C/C++ compiler (for building the parser)
- tree-sitter CLI: `npm install -g tree-sitter-cli` or `cargo install tree-sitter-cli`

### Building the Parser

```bash
# Clone or navigate to the parser directory
cd tree-sitter-dml

# Install dependencies
npm install

# Generate the parser
tree-sitter generate

# Run tests
tree-sitter test

# Try parsing a DML file
tree-sitter parse path/to/file.dml
```

## Usage

### Command Line

```bash
# Parse a DML file and display the syntax tree
tree-sitter parse example.dml

# Run the test suite
tree-sitter test

# Run specific tests
tree-sitter test -i "Device declaration"

# Start the playground
tree-sitter playground
```

### Node.js

```javascript
const Parser = require('tree-sitter');
const DML = require('tree-sitter-dml');

const parser = new Parser();
parser.setLanguage(DML);

const sourceCode = `
device my_device;

bank regs {
    register status size 4 @ 0x00 {
        field ready @ [0];
        field error @ [1];
    }
}
`;

const tree = parser.parse(sourceCode);
console.log(tree.rootNode.toString());
```

### Python

```python
from tree_sitter import Language, Parser

# Build the language
Language.build_library(
    'build/dml.so',
    ['tree-sitter-dml']
)

# Load and use
DML_LANGUAGE = Language('build/dml.so', 'dml')
parser = Parser()
parser.set_language(DML_LANGUAGE)

source_code = b"""
device my_device;

bank regs {
    register status size 4 @ 0x00;
}
"""

tree = parser.parse(source_code)
print(tree.root_node.sexp())
```

## Grammar Reference

### Top-Level Structure

```dml
[provisional identifier_list;]
[device identifier;]
[bitorder (be|le);]
device_statement*
```

### Object Hierarchy

```
device
├── bank
│   ├── register
│   │   └── field
│   └── group
├── port
│   └── implement
├── attribute
├── connect
├── event
└── subdevice
```

### Example DML Code

```dml
device uart;
bitorder le;

import "dml-builtins.dml";

template my_register {
    param size = 4;
    
    method after_write(uint64 value) {
        log info: "Written: 0x%x", value;
    }
}

bank regs {
    register ctrl size 4 @ 0x00 is (my_register) {
        field enable @ [0];
        field mode @ [2:1];
        
        method after_write(uint64 value) {
            if (this.enable == 1) {
                log info: "UART enabled";
            }
        }
    }
    
    register data size 4 @ 0x04 is (my_register);
}

method init() {
    log info: "UART device initialized";
}
```

## Testing

The parser includes comprehensive test coverage in `test/corpus/`:

- **basic.txt**: Device declarations, registers, fields, templates, imports
- **statements.txt**: Control flow, loops, error handling, logging
- **expressions.txt**: Operators, member access, function calls, type operations

Run tests with:

```bash
tree-sitter test
```

## Development

### Project Structure

```
tree-sitter-dml/
├── grammar.js              # Grammar definition
├── package.json            # Node.js package config
├── tree-sitter.json        # Tree-sitter config
├── src/                    # Generated parser (after tree-sitter generate)
│   ├── parser.c
│   └── tree_sitter/
├── test/
│   └── corpus/             # Test files
│       ├── basic.txt
│       ├── statements.txt
│       └── expressions.txt
└── README.md
```

### Adding New Tests

Create test files in `test/corpus/` with the format:

```
==================
Test name
==================

input DML code

---

(expected
  (syntax
    (tree)))
```

### Modifying the Grammar

1. Edit `grammar.js`
2. Run `tree-sitter generate` to regenerate the parser
3. Run `tree-sitter test` to verify changes
4. Add tests for new features

## Language Bindings

This parser can be used with Tree-sitter bindings for:

- **C/C++**: Native integration
- **Node.js**: JavaScript/TypeScript
- **Python**: Via tree-sitter Python bindings
- **Rust**: Via tree-sitter Rust crate
- **Go**: Via tree-sitter Go bindings

## References

- [DML 1.4 Reference Manual](https://www.intel.com/content/www/us/en/developer/articles/guide/simics-reference-manual.html)
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Intel Simics](https://www.intel.com/content/www/us/en/developer/articles/tool/simics-simulator.html)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License

## Author

wangli-ustc

## Acknowledgments

Based on the DML 1.4 specification from Intel Simics and the official DML compiler (dmlc) version 7.57.0.
