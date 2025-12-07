#!/usr/bin/env python3
"""
Test script for code summarization with DashScope/Qwen3-coder-plus.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.code_summarizer import generate_file_summary, generate_chunk_summary
try:
    from llms.dashscope_client import test_dashscope_connection
except ImportError:
    from dashscope_client import test_dashscope_connection


# Sample DML code
DML_CODE = """
dml 1.4;

device uart_controller;
bitorder le;

constant FIFO_SIZE = 16;
constant BAUD_RATE = 115200;

// Template for registers with logging
template logged_register {
    param size = 4;
    
    method after_write(uint64 value) {
        log info: "Register %s written: 0x%x", qname, value;
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
                }
            }
        }
        field mode @ [2:1];
        field loopback @ [3];
    }
    
    // Status register
    register status size 4 @ 0x04 {
        field tx_ready @ [0];
        field rx_ready @ [1];
        field tx_empty @ [2];
        field rx_full @ [3];
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
}

// FIFO buffer
data uint8 rx_fifo[FIFO_SIZE];
data uint32 rx_head;
data uint32 rx_tail;

method init() {
    log info: "Initializing UART controller";
    regs.ctrl.enable = 0;
    regs.status.tx_ready = 1;
    rx_head = 0;
    rx_tail = 0;
}

method transmit_byte(uint8 byte) {
    if (regs.status.tx_ready == 0) {
        log error: "Transmit buffer full";
        return;
    }
    log info: "Transmitting byte: 0x%02x", byte;
    regs.status.tx_ready = 0;
}

method receive_byte() -> (uint8) {
    if (rx_head == rx_tail) {
        log warning: "Receive buffer empty";
        return 0;
    }
    local uint8 byte = rx_fifo[rx_tail];
    rx_tail = (rx_tail + 1) % FIFO_SIZE;
    return byte;
}
"""

# Sample Python code
PYTHON_CODE = """
import simics
from simics import SIM_get_attribute, SIM_set_attribute

class UARTDevice:
    '''
    UART device implementation for Simics.
    Provides serial communication functionality.
    '''
    
    def __init__(self, obj):
        self.obj = obj
        self.baud_rate = 115200
        self.tx_buffer = []
        self.rx_buffer = []
        
    def reset(self):
        '''Reset the UART device to initial state.'''
        self.tx_buffer.clear()
        self.rx_buffer.clear()
        print(f"UART device {self.obj.name} reset")
        
    def transmit(self, data):
        '''Transmit data through UART.'''
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.tx_buffer.extend(data)
        self._process_tx()
        
    def _process_tx(self):
        '''Process transmit buffer.'''
        while self.tx_buffer:
            byte = self.tx_buffer.pop(0)
            # Simulate transmission delay
            SIM_get_attribute(self.obj, "serial_device").write(byte)
            
    def receive(self, byte):
        '''Receive a byte from external source.'''
        self.rx_buffer.append(byte)
        # Trigger interrupt if enabled
        if SIM_get_attribute(self.obj, "interrupt_enabled"):
            self._trigger_interrupt()
            
    def _trigger_interrupt(self):
        '''Trigger receive interrupt.'''
        cpu = SIM_get_attribute(self.obj, "cpu")
        SIM_set_attribute(cpu, "pending_interrupt", True)
"""


def test_dml_summarization():
    """Test DML code summarization."""
    print("=" * 70)
    print("Testing DML Code Summarization")
    print("=" * 70)
    
    metadata = {
        'language': 'dml',
        'file_path': 'devices/uart_controller.dml',
        'device_name': 'uart_controller',
        'line_count': len(DML_CODE.split('\n'))
    }
    
    print("\n1. Generating file-level summary...")
    try:
        file_summary = generate_file_summary(DML_CODE, metadata)
        print(f"   ✓ File Summary:")
        print(f"     {file_summary}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test chunk summarization
    chunk_code = """
bank regs {
    register ctrl size 4 @ 0x00 is (logged_register) {
        field enable @ [0];
        field mode @ [2:1];
        field loopback @ [3];
    }
    
    register status size 4 @ 0x04 {
        field tx_ready @ [0];
        field rx_ready @ [1];
    }
}
"""
    
    chunk_metadata = metadata.copy()
    chunk_metadata['chunk_type'] = 'register_definitions'
    
    print("\n2. Generating chunk-level summary...")
    try:
        chunk_summary = generate_chunk_summary(chunk_code, file_summary, chunk_metadata)
        print(f"   ✓ Chunk Summary:")
        print(f"     {chunk_summary}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    return True


def test_python_summarization():
    """Test Python code summarization."""
    print("\n" + "=" * 70)
    print("Testing Python Code Summarization")
    print("=" * 70)
    
    metadata = {
        'language': 'python',
        'file_path': 'modules/uart_device.py',
        'line_count': len(PYTHON_CODE.split('\n'))
    }
    
    print("\n1. Generating file-level summary...")
    try:
        file_summary = generate_file_summary(PYTHON_CODE, metadata)
        print(f"   ✓ File Summary:")
        print(f"     {file_summary}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test chunk summarization
    chunk_code = """
def transmit(self, data):
    '''Transmit data through UART.'''
    if isinstance(data, str):
        data = data.encode('utf-8')
    self.tx_buffer.extend(data)
    self._process_tx()
    
def _process_tx(self):
    '''Process transmit buffer.'''
    while self.tx_buffer:
        byte = self.tx_buffer.pop(0)
        SIM_get_attribute(self.obj, "serial_device").write(byte)
"""
    
    chunk_metadata = metadata.copy()
    chunk_metadata['chunk_type'] = 'method_definitions'
    
    print("\n2. Generating chunk-level summary...")
    try:
        chunk_summary = generate_chunk_summary(chunk_code, file_summary, chunk_metadata)
        print(f"   ✓ Chunk Summary:")
        print(f"     {chunk_summary}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("\n🧪 Testing Code Summarization with DashScope/Qwen3-coder-plus\n")
    
    # Check environment
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ DASHSCOPE_API_KEY not set in environment")
        print("   Please set it in .env file or export it:")
        print("   export DASHSCOPE_API_KEY=your_api_key")
        return 1
    
    # Test connection
    print("Testing DashScope connection...")
    if not test_dashscope_connection():
        print("\n❌ DashScope connection failed. Please check your API key.")
        return 1
    
    print()
    
    # Run tests
    results = {
        "DML Summarization": test_dml_summarization(),
        "Python Summarization": test_python_summarization()
    }
    
    # Print results
    print("\n" + "=" * 70)
    print("Test Results")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print("\nThe hybrid summarization approach is working correctly!")
        print("You can now run crawl_simics_source.py with USE_CODE_SUMMARIZATION=true")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
