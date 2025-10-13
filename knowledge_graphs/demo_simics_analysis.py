#!/usr/bin/env python3
"""
Demo script for Simics Neo4j Integration

This script demonstrates how to use the Simics Neo4j integration to analyze
DML code and Python tests. It can work with or without an actual Neo4j database.

Usage:
    python demo_simics_analysis.py --demo-parsing
    python demo_simics_analysis.py --analyze-path /path/to/simics/
    python demo_simics_analysis.py --neo4j-demo  # requires Neo4j running
"""

import argparse
import asyncio
import tempfile
from pathlib import Path
import sys

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from simics_dml_parser import DMLParser


def create_demo_dml_files(demo_dir: Path):
    """Create demo DML files for testing"""
    
    # Base device
    base_dml = '''
device base_device {
    attribute clock_freq : uint64 = 100000000;
    
    method init() {
        // Base initialization
    }
    
    method reset() {
        // Reset device
    }
}
'''
    
    # UART device
    uart_dml = '''
import "base_device.dml";

device uart_device : base_device {
    implement uart_interface;
    
    attribute baud_rate : uint32 = 115200;
    attribute buffer_size : uint32 = 1024;
    attribute flow_control : bool = false;
    
    register control @ 0x00 size 4 {
        field enable @ [0];
        field reset @ [1];
        field interrupt_enable @ [2];
    }
    
    register status @ 0x04 size 4 {
        field ready @ [0];
        field error @ [1];
        field busy @ [2];
    }
    
    register data @ 0x08 size 4;
    
    method write_data(value) {
        // Write data to UART
    }
    
    method read_data() -> (value) {
        // Read data from UART
    }
    
    method configure_baud(rate) {
        // Configure baud rate
    }
}

interface uart_interface {
    method send_byte(data);
    method receive_byte() -> (data);
    method set_config(config);
}
'''
    
    # Enhanced UART with inheritance
    enhanced_uart_dml = '''
import "uart_device.dml";

device enhanced_uart : uart_device {
    attribute dma_enabled : bool = false;
    attribute fifo_size : uint32 = 256;
    
    register dma_control @ 0x10 size 4 {
        field dma_enable @ [0];
        field dma_direction @ [1];
        field dma_burst_size @ [4:2];
    }
    
    register fifo_control @ 0x14 size 4 {
        field fifo_enable @ [0];
        field fifo_reset @ [1];
        field fifo_threshold @ [7:4];
    }
    
    method setup_dma(address, size) {
        // Setup DMA transfer
    }
    
    method configure_fifo(threshold) {
        // Configure FIFO settings
    }
    
    method handle_interrupt() {
        // Handle enhanced interrupt features
    }
}
'''
    
    # Memory controller
    memory_dml = '''
import "base_device.dml";

device memory_controller : base_device {
    implement memory_interface;
    
    attribute memory_size : uint64 = 0x100000000;  // 4GB
    attribute cache_enabled : bool = true;
    
    register base_address @ 0x00 size 8;
    register size_register @ 0x08 size 8;
    register control_reg @ 0x10 size 4 {
        field enable @ [0];
        field cache_enable @ [1];
        field protection_enable @ [2];
    }
    
    method map_memory(base, size) {
        // Map memory region
    }
    
    method read_memory(address) -> (data) {
        // Read from memory
    }
    
    method write_memory(address, data) {
        // Write to memory
    }
}

interface memory_interface {
    method allocate(size) -> (address);
    method deallocate(address);
    method get_info() -> (info);
}
'''
    
    # Write demo files
    (demo_dir / "base_device.dml").write_text(base_dml)
    (demo_dir / "uart_device.dml").write_text(uart_dml)
    (demo_dir / "enhanced_uart.dml").write_text(enhanced_uart_dml)
    (demo_dir / "memory_controller.dml").write_text(memory_dml)


def create_demo_test_files(demo_dir: Path):
    """Create demo test files"""
    
    test_uart = '''
import pytest
import simics
from simics import SIM_create_object, SIM_run_command
from pyobj import conf

@pytest.fixture
def uart_device():
    """Create UART device for testing"""
    device = SIM_create_object("uart_device", "test_uart", [])
    yield device

@pytest.fixture(scope="session")  
def simulation():
    """Setup simulation environment"""
    simics.SIM_load_module("uart_module")
    yield

def test_uart_basic_functionality(uart_device, simulation):
    """Test basic UART functionality"""
    # Test device creation
    assert uart_device is not None
    
    # Test attribute access
    conf.test_uart.baud_rate = 9600
    assert conf.test_uart.baud_rate == 9600
    
    # Test register access
    simics.SIM_write_register(uart_device, "control", 0x1)
    control_val = simics.SIM_read_register(uart_device, "control")
    assert control_val & 0x1 == 1

def test_uart_data_transmission(uart_device):
    """Test UART data transmission"""
    test_data = b"Hello UART"
    
    # Write test data
    for byte in test_data:
        uart_device.send_byte(byte)
    
    # Read back data
    received = []
    for _ in range(len(test_data)):
        received.append(uart_device.receive_byte())
    
    assert bytes(received) == test_data

def test_uart_error_conditions(uart_device):
    """Test UART error handling"""
    # Test buffer overflow
    large_data = b"x" * 2048  # Larger than buffer
    
    try:
        for byte in large_data:
            uart_device.send_byte(byte)
    except Exception as e:
        assert "buffer" in str(e).lower()

class TestUARTAdvanced:
    """Advanced UART test suite"""
    
    def test_interrupt_handling(self, uart_device):
        """Test UART interrupt functionality"""
        # Enable interrupts
        simics.SIM_write_register(uart_device, "control", 0x4)
        
        # Trigger interrupt condition
        uart_device.send_byte(0xFF)
        
        # Check interrupt status
        status = simics.SIM_read_register(uart_device, "status")
        assert status & 0x4 != 0  # Interrupt bit set
    
    def test_performance_benchmark(self, uart_device):
        """Benchmark UART performance"""
        import time
        
        start_time = time.time()
        
        # Send 1000 bytes
        for i in range(1000):
            uart_device.send_byte(i % 256)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        assert duration < 1.0
        
        throughput = 1000 / duration
        print(f"UART throughput: {throughput:.0f} bytes/sec")
'''
    
    test_memory = '''
import pytest
import simics
from simics import SIM_create_object

@pytest.fixture
def memory_controller():
    """Create memory controller for testing"""
    device = SIM_create_object("memory_controller", "test_memory", [])
    yield device

def test_memory_allocation(memory_controller):
    """Test memory allocation"""
    # Allocate memory block
    address = memory_controller.allocate(4096)
    assert address is not None
    assert address > 0
    
    # Deallocate
    memory_controller.deallocate(address)

def test_memory_read_write(memory_controller):
    """Test memory read/write operations"""
    test_address = 0x1000
    test_data = 0xDEADBEEF
    
    # Write data
    memory_controller.write_memory(test_address, test_data)
    
    # Read back
    read_data = memory_controller.read_memory(test_address)
    assert read_data == test_data

def test_memory_mapping(memory_controller):
    """Test memory mapping functionality"""
    base_address = 0x80000000
    size = 0x10000000  # 256MB
    
    memory_controller.map_memory(base_address, size)
    
    # Verify mapping
    info = memory_controller.get_info()
    assert info["base_address"] == base_address
    assert info["size"] == size
'''
    
    # Create test directory and files
    test_dir = demo_dir / "tests"
    test_dir.mkdir(exist_ok=True)
    
    (test_dir / "test_uart.py").write_text(test_uart)
    (test_dir / "test_memory.py").write_text(test_memory)


def demo_parsing():
    """Demonstrate DML parsing capabilities"""
    print("🔧 DML Parsing Demo")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_dir = Path(temp_dir)
        
        print("📁 Creating demo DML files...")
        create_demo_dml_files(demo_dir)
        
        print("🔍 Analyzing DML files...")
        parser = DMLParser()
        
        dml_files = list(demo_dir.glob("*.dml"))
        total_stats = {
            'devices': 0,
            'interfaces': 0, 
            'methods': 0,
            'attributes': 0,
            'registers': 0
        }
        
        for dml_file in dml_files:
            print(f"\n📄 Analyzing: {dml_file.name}")
            
            result = parser.parse_dml_file(dml_file, demo_dir)
            
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
                continue
            
            # Display results
            print(f"  📦 Devices: {len(result['devices'])}")
            for device in result['devices']:
                parent_info = f" (inherits from {device.parent})" if device.parent else ""
                print(f"    • {device.name}{parent_info}")
            
            print(f"  🔌 Interfaces: {len(result['interfaces'])}")
            for interface in result['interfaces']:
                print(f"    • {interface.name}")
            
            print(f"  ⚙️  Methods: {len(result['methods'])}")
            for method in result['methods'][:5]:  # Show first 5
                params = ", ".join(method.parameters) if method.parameters else ""
                print(f"    • {method.name}({params}) in {method.device}")
            
            print(f"  📊 Attributes: {len(result['attributes'])}")
            for attr in result['attributes'][:5]:  # Show first 5
                print(f"    • {attr.name}: {attr.type_name} in {attr.device}")
            
            print(f"  🗂️  Registers: {len(result['registers'])}")
            for reg in result['registers'][:5]:  # Show first 5
                size_info = f" (size {reg.size})" if reg.size else ""
                print(f"    • {reg.name} @ {reg.address}{size_info} in {reg.device}")
            
            # Update totals
            total_stats['devices'] += len(result['devices'])
            total_stats['interfaces'] += len(result['interfaces'])
            total_stats['methods'] += len(result['methods'])
            total_stats['attributes'] += len(result['attributes'])
            total_stats['registers'] += len(result['registers'])
        
        print(f"\n📊 Total Statistics:")
        print(f"  Files analyzed: {len(dml_files)}")
        print(f"  Devices: {total_stats['devices']}")
        print(f"  Interfaces: {total_stats['interfaces']}")
        print(f"  Methods: {total_stats['methods']}")
        print(f"  Attributes: {total_stats['attributes']}")
        print(f"  Registers: {total_stats['registers']}")


def demo_file_analysis(path: str):
    """Demonstrate analysis of real files"""
    print(f"📁 File Analysis Demo: {path}")
    print("=" * 50)
    
    analysis_path = Path(path)
    if not analysis_path.exists():
        print(f"❌ Path not found: {path}")
        return
    
    # Find DML files
    dml_files = list(analysis_path.rglob("*.dml"))
    test_files = []
    
    # Find test files
    for pattern in ["test_*.py", "*_test.py"]:
        test_files.extend(analysis_path.rglob(pattern))
    
    print(f"🔍 Discovery Results:")
    print(f"  DML files: {len(dml_files)}")
    print(f"  Test files: {len(test_files)}")
    
    if dml_files:
        print(f"\n🔧 Analyzing up to 5 DML files...")
        parser = DMLParser()
        
        for i, dml_file in enumerate(dml_files[:5], 1):
            print(f"\n[{i}] {dml_file.relative_to(analysis_path)}")
            
            try:
                result = parser.parse_dml_file(dml_file, analysis_path)
                
                if 'error' in result:
                    print(f"    ❌ Parse error: {result['error']}")
                    continue
                
                print(f"    ✅ Parsed successfully")
                print(f"    📦 {len(result['devices'])} devices, {len(result['methods'])} methods")
                
                # Show device names
                if result['devices']:
                    device_names = [d.name for d in result['devices'][:3]]
                    if len(result['devices']) > 3:
                        device_names.append(f"... and {len(result['devices']) - 3} more")
                    print(f"    🏷️  Devices: {', '.join(device_names)}")
                
            except Exception as e:
                print(f"    💥 Analysis failed: {e}")
    
    if test_files:
        print(f"\n🧪 Found {len(test_files)} test files")
        for test_file in test_files[:5]:
            print(f"    • {test_file.relative_to(analysis_path)}")
        if len(test_files) > 5:
            print(f"    ... and {len(test_files) - 5} more")


async def demo_neo4j():
    """Demonstrate Neo4j integration (requires running Neo4j)"""
    print("🗄️  Neo4j Integration Demo")
    print("=" * 50)
    
    try:
        # This would require Neo4j to be running
        print("This demo requires Neo4j to be running.")
        print("To use the full Neo4j integration:")
        print()
        print("1. Start Neo4j:")
        print("   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest")
        print()
        print("2. Set password:")
        print("   export NEO4J_PASSWORD=password")
        print()
        print("3. Run analysis:")
        print("   python parse_simics_into_neo4j.py --local-path /path/to/simics/")
        print()
        print("4. Query the graph:")
        print("   python query_simics_knowledge_graph.py --query stats")
        print("   python query_simics_knowledge_graph.py --interactive")
        
    except Exception as e:
        print(f"❌ Neo4j demo failed: {e}")


def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(
        description="Demo Simics Neo4j Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_simics_analysis.py --demo-parsing
  python demo_simics_analysis.py --analyze-path /path/to/simics/
  python demo_simics_analysis.py --neo4j-demo
        """
    )
    
    parser.add_argument('--demo-parsing', action='store_true', 
                       help='Demo DML parsing with sample files')
    parser.add_argument('--analyze-path', help='Analyze DML files in given path')
    parser.add_argument('--neo4j-demo', action='store_true',
                       help='Show Neo4j integration instructions')
    
    args = parser.parse_args()
    
    if args.demo_parsing:
        demo_parsing()
    elif args.analyze_path:
        demo_file_analysis(args.analyze_path)
    elif args.neo4j_demo:
        asyncio.run(demo_neo4j())
    else:
        print("Please specify one of the demo options. Use --help for details.")


if __name__ == "__main__":
    main()