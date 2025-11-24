#!/usr/bin/env python3
"""
Demo script showing DML code chunking with astchunk.

This demonstrates how the updated astchunk library can parse and chunk
DML (Device Modeling Language) source code using tree-sitter-dml.
"""

import sys
from pathlib import Path

# Add astchunk to path
astchunk_path = Path(__file__).parent / 'astchunk' / 'src'
sys.path.insert(0, str(astchunk_path))

# Add tree-sitter-dml to path (fallback if not installed)
dml_path = Path(__file__).parent / "tree-sitter-dml"
if dml_path.exists():
    sys.path.insert(0, str(dml_path / "bindings" / "python"))

# Sample DML code
DML_CODE = """
dml 1.4;

device uart_controller;

import "utility.dml";

constant FIFO_SIZE = 16;
constant BAUD_RATE = 115200;

// Template for registers with logging
template logged_register {
    param size = 4;
    
    method after_write(uint64 value) {
        log info: "Register %s written: 0x%x", qname, value;
    }
    
    method after_read(uint64 value) -> (uint64) {
        log info: "Register %s read: 0x%x", qname, value;
        return value;
    }
}

// UART register bank
bank regs {
    // Control register
    register ctrl size 4 @ 0x00 is (logged_register) {
        field enable @ [0] {
            method write(uint1 value) {
                this.val = value;
                if (value == 1) {
                    log info: "UART enabled";
                    call $init_uart();
                } else {
                    log info: "UART disabled";
                }
            }
        }
        
        field mode @ [2:1] {
            // 0: 8N1, 1: 7E1, 2: 8E1, 3: 8O1
        }
        
        field loopback @ [3];
    }
    
    // Status register (read-only)
    register status size 4 @ 0x04 {
        field tx_ready @ [0];
        field rx_ready @ [1];
        field tx_empty @ [2];
        field rx_full @ [3];
        field error @ [7:4];
    }
    
    // Data register
    register data size 4 @ 0x08 is (logged_register) {
        method write(uint64 value) {
            call $transmit_byte(value & 0xFF);
        }
        
        method read() -> (uint64) {
            return call $receive_byte();
        }
    }
    
    // Baud rate divisor
    register baud_div size 4 @ 0x0C is (logged_register);
}

// FIFO buffer for received data
data uint8 rx_fifo[FIFO_SIZE];
data uint32 rx_head;
data uint32 rx_tail;

// Initialize UART
method init() {
    log info: "Initializing UART controller";
    regs.ctrl.enable = 0;
    regs.status.tx_ready = 1;
    regs.status.tx_empty = 1;
    regs.status.rx_ready = 0;
    regs.status.rx_full = 0;
    rx_head = 0;
    rx_tail = 0;
}

// Internal method to initialize UART hardware
method init_uart() {
    local uint32 divisor = 50000000 / BAUD_RATE;
    regs.baud_div.val = divisor;
    log info: "UART initialized with baud divisor: %d", divisor;
}

// Transmit a byte
method transmit_byte(uint8 byte) {
    if (regs.status.tx_ready == 0) {
        log error: "Transmit buffer full, dropping byte";
        return;
    }
    
    log info: "Transmitting byte: 0x%02x", byte;
    regs.status.tx_ready = 0;
    
    // Simulate transmission delay
    after (1.0 / BAUD_RATE) s: {
        regs.status.tx_ready = 1;
        regs.status.tx_empty = 1;
    }
}

// Receive a byte
method receive_byte() -> (uint8) {
    if (rx_head == rx_tail) {
        log warning: "Receive buffer empty";
        return 0;
    }
    
    local uint8 byte = rx_fifo[rx_tail];
    rx_tail = (rx_tail + 1) % FIFO_SIZE;
    
    if (rx_head == rx_tail) {
        regs.status.rx_ready = 0;
    }
    regs.status.rx_full = 0;
    
    log info: "Received byte: 0x%02x", byte;
    return byte;
}

// Handle incoming data (called by simulation)
method push_rx_byte(uint8 byte) {
    local uint32 next_head = (rx_head + 1) % FIFO_SIZE;
    
    if (next_head == rx_tail) {
        log error: "Receive FIFO full, dropping byte";
        regs.status.error = regs.status.error | 0x1;
        return;
    }
    
    rx_fifo[rx_head] = byte;
    rx_head = next_head;
    regs.status.rx_ready = 1;
    
    if (next_head == rx_tail) {
        regs.status.rx_full = 1;
    }
}
"""

def main():
    """Demonstrate DML code chunking."""
    print("=" * 70)
    print("DML Code Chunking Demo with ASTChunk")
    print("=" * 70)
    print()
    
    try:
        from astchunk import ASTChunkBuilder
        
        print("✓ Successfully imported ASTChunkBuilder")
        print()
        
        # Create chunker for DML
        print("Creating DML chunker with max_chunk_size=800...")
        chunker = ASTChunkBuilder(
            max_chunk_size=800,
            language="dml",
            metadata_template="default"
        )
        print("✓ DML chunker created successfully")
        print()
        
        # Chunk the DML code
        print("Chunking DML code...")
        chunks = chunker.chunkify(
            code=DML_CODE,
            chunk_overlap=1,
            chunk_expansion=False,
            repo_level_metadata={
                "file_path": "uart_controller.dml",
                "device": "uart_controller"
            }
        )
        
        print(f"✓ Generated {len(chunks)} chunks")
        print()
        
        # Display chunk information
        print("=" * 70)
        print("Chunk Details")
        print("=" * 70)
        print()
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            print(f"Chunk {i}:")
            print(f"  Size: {len(content)} characters")
            print(f"  Non-whitespace: {len(content.replace(' ', '').replace('\\n', '').replace('\\t', ''))} chars")
            
            if metadata:
                if 'start_line' in metadata:
                    print(f"  Lines: {metadata['start_line']}-{metadata['end_line']}")
                if 'file_path' in metadata:
                    print(f"  File: {metadata['file_path']}")
            
            # Show first few lines
            lines = content.split('\\n')[:5]
            print(f"  Preview:")
            for line in lines:
                if line.strip():
                    print(f"    {line[:70]}")
            
            if len(content.split('\\n')) > 5:
                print(f"    ... ({len(content.split('\\n')) - 5} more lines)")
            
            print()
        
        print("=" * 70)
        print("✓ Demo completed successfully!")
        print("=" * 70)
        
        return 0
        
    except ImportError as e:
        print(f"✗ Failed to import astchunk: {e}")
        print()
        print("Please ensure astchunk is in the Python path:")
        print("  export PYTHONPATH=$PYTHONPATH:./astchunk/src")
        return 1
        
    except ValueError as e:
        error_msg = str(e)
        if "tree-sitter-dml" in error_msg:
            print(f"✗ {e}")
            print()
            print("To install tree-sitter-dml:")
            print("  pip install -e tree-sitter-dml")
            print()
            print("Or ensure tree-sitter-dml directory exists with Python bindings")
        else:
            print(f"✗ Error: {e}")
        return 1
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
