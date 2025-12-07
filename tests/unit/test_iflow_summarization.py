#!/usr/bin/env python3
"""
Test iFlow-based code summarization.
Verifies that the iFlow API integration works correctly for code summarization.
"""
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from llms.iflow_client import test_iflow_connection
except ImportError:
    from iflow_client import test_iflow_connection
from core.code_summarizer import generate_file_summary, generate_chunk_summary


def test_iflow_api():
    """Test basic iFlow API connectivity."""
    print("=" * 60)
    print("Testing iFlow API Connection")
    print("=" * 60)
    
    success = test_iflow_connection()
    
    if not success:
        print("\n❌ iFlow API connection failed!")
        print("Please check:")
        print("  1. IFLOW_API_KEY is set in .env")
        print("  2. IFLOW_BASE_URL is correct (default: https://api.iflow.cn/v1)")
        print("  3. Your API key is valid and has access to iflow/qwen3-coder-plus")
        return False
    
    print("\n✅ iFlow API connection successful!\n")
    return True


def test_file_summarization():
    """Test file-level summarization with iFlow."""
    print("=" * 60)
    print("Testing File-Level Summarization")
    print("=" * 60)
    
    # Sample DML code
    dml_code = """
dml 1.4;

device uart_16550;

import "utility.dml";

constant FIFO_SIZE = 16;

bank regs {
    register RBR size 1 @ 0x00 "Receiver Buffer Register" {
        field data @ [7:0];
    }
    
    register THR size 1 @ 0x00 "Transmitter Holding Register" {
        field data @ [7:0];
    }
    
    register IER size 1 @ 0x01 "Interrupt Enable Register" {
        field erbfi @ [0] "Enable Received Data Available Interrupt";
        field etbei @ [1] "Enable Transmitter Holding Register Empty Interrupt";
        field elsi @ [2] "Enable Receiver Line Status Interrupt";
        field edssi @ [3] "Enable Modem Status Interrupt";
    }
    
    register LSR size 1 @ 0x05 "Line Status Register" {
        field dr @ [0] "Data Ready";
        field oe @ [1] "Overrun Error";
        field pe @ [2] "Parity Error";
        field fe @ [3] "Framing Error";
        field bi @ [4] "Break Interrupt";
        field thre @ [5] "Transmitter Holding Register Empty";
        field temt @ [6] "Transmitter Empty";
        field fifo_error @ [7] "Error in RCVR FIFO";
    }
}

method init() {
    log info: "UART 16550 initialized";
    regs.LSR.thre = 1;
    regs.LSR.temt = 1;
}

method write_data(uint8 data) {
    log info: "Transmitting byte: 0x%02x", data;
    // Simulate transmission
    call transmit_byte(data);
}

method transmit_byte(uint8 data) {
    // Hardware transmission logic
    regs.LSR.thre = 0;
    after (1ms) call transmission_complete();
}

method transmission_complete() {
    regs.LSR.thre = 1;
    regs.LSR.temt = 1;
    if (regs.IER.etbei) {
        // Trigger interrupt
        log info: "Triggering TX interrupt";
    }
}
"""
    
    metadata = {
        'language': 'dml',
        'file_path': 'devices/uart_16550.dml',
        'device_name': 'uart_16550',
        'line_count': 60,
        'char_count': len(dml_code)
    }
    
    print("\n📄 Generating file summary for UART 16550 device...")
    print(f"   File: {metadata['file_path']}")
    print(f"   Device: {metadata['device_name']}")
    print(f"   Size: {metadata['line_count']} lines, {metadata['char_count']} chars")
    
    try:
        summary = generate_file_summary(dml_code, metadata)
        print(f"\n✅ File Summary Generated:")
        print(f"   {summary}")
        return True
    except Exception as e:
        print(f"\n❌ File summarization failed: {e}")
        return False


def test_chunk_summarization():
    """Test chunk-level summarization with iFlow."""
    print("\n" + "=" * 60)
    print("Testing Chunk-Level Summarization")
    print("=" * 60)
    
    file_summary = "UART 16550 device model implementing a standard serial communication controller with FIFO buffers, interrupt handling, and line status monitoring."
    
    chunk_code = """
bank regs {
    register LSR size 1 @ 0x05 "Line Status Register" {
        field dr @ [0] "Data Ready";
        field oe @ [1] "Overrun Error";
        field pe @ [2] "Parity Error";
        field fe @ [3] "Framing Error";
        field bi @ [4] "Break Interrupt";
        field thre @ [5] "Transmitter Holding Register Empty";
        field temt @ [6] "Transmitter Empty";
        field fifo_error @ [7] "Error in RCVR FIFO";
    }
}
"""
    
    metadata = {
        'language': 'dml',
        'device_name': 'uart_16550',
        'chunk_type': 'register_definition'
    }
    
    print("\n📦 Generating chunk summary for LSR register...")
    print(f"   Chunk Type: {metadata['chunk_type']}")
    print(f"   File Context: {file_summary[:80]}...")
    
    try:
        summary = generate_chunk_summary(chunk_code, file_summary, metadata)
        print(f"\n✅ Chunk Summary Generated:")
        print(f"   {summary}")
        return True
    except Exception as e:
        print(f"\n❌ Chunk summarization failed: {e}")
        return False


def main():
    """Run all tests."""
    load_dotenv()
    
    print("\n🚀 iFlow Code Summarization Test Suite")
    print("=" * 60)
    
    # Check if iFlow is configured
    if not os.getenv("IFLOW_API_KEY"):
        print("\n❌ IFLOW_API_KEY not found in environment!")
        print("Please set IFLOW_API_KEY in your .env file")
        return False
    
    # Test 1: API Connection
    if not test_iflow_api():
        return False
    
    # Test 2: File Summarization
    if not test_file_summarization():
        return False
    
    # Test 3: Chunk Summarization
    if not test_chunk_summarization():
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\niFlow integration is working correctly.")
    print("You can now use code summarization with iflow/qwen3-coder-plus model.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
