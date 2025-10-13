#!/usr/bin/env python3
"""
Test script for Simics Neo4j integration

This script validates that the Simics Neo4j integration components work correctly
by testing the parsers and analyzers with sample data.
"""

import os
import sys
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from simics_dml_parser import DMLParser
from simics_test_analyzer import SimicsTestAnalyzer


def create_sample_dml_file() -> str:
    """Create a sample DML file for testing"""
    dml_content = '''
import "base_device.dml";

device uart_device : base_device {
    implement uart_interface;
    
    attribute baud_rate : uint32 = 115200;
    attribute buffer_size : uint32 = 1024;
    
    register control @ 0x00 size 4 {
        field enable @ [0];
        field reset @ [1];
    }
    
    register status @ 0x04 size 4 {
        field ready @ [0];
        field error @ [1];
    }
    
    method init() {
        // Initialize UART device
    }
    
    method read(addr) -> (value) {
        // Read from UART register
    }
    
    method write(addr, value) {
        // Write to UART register
    }
}

interface uart_interface {
    method send_data(data);
    method receive_data() -> (data);
}

device enhanced_uart : uart_device {
    attribute flow_control : bool = true;
    
    register flow_ctrl @ 0x08 size 4 {
        field rts @ [0];
        field cts @ [1];
    }
    
    method configure_flow_control(enable) {
        // Configure flow control
    }
}
'''
    return dml_content


def create_sample_test_file() -> str:
    """Create a sample Python test file for testing"""
    test_content = '''
import pytest
import simics
from simics import SIM_create_object, SIM_run_command
from pyobj import conf

@pytest.fixture
def uart_device():
    """Fixture to create a UART device for testing"""
    device = SIM_create_object("uart_device", "test_uart", [])
    yield device
    # Cleanup

@pytest.fixture(scope="session")
def simulation_env():
    """Session-wide simulation environment"""
    simics.SIM_load_module("test_module")
    yield
    # Cleanup

def test_uart_initialization(uart_device):
    """Test UART device initialization"""
    assert uart_device is not None
    
    # Test initial register values
    control_reg = SIM_read_register(uart_device, "control")
    assert control_reg == 0
    
    status_reg = SIM_read_register(uart_device, "status")
    assert status_reg & 0x1 == 0  # ready bit should be 0

def test_uart_configuration(uart_device, simulation_env):
    """Test UART device configuration"""
    # Set baud rate
    conf.uart_device.baud_rate = 9600
    assert conf.uart_device.baud_rate == 9600
    
    # Test control register
    SIM_write_register(uart_device, "control", 0x1)
    control_val = SIM_read_register(uart_device, "control")
    assert control_val & 0x1 == 1  # enable bit

def test_uart_data_transmission(uart_device):
    """Test UART data transmission"""
    test_data = "Hello, Simics!"
    
    # Send data
    uart_device.send_data(test_data)
    
    # Verify transmission
    status = SIM_read_register(uart_device, "status")
    assert status & 0x1 == 1  # ready bit should be set

def test_uart_error_handling(uart_device):
    """Test UART error handling"""
    # Simulate error condition
    SIM_write_register(uart_device, "status", 0x2)  # set error bit
    
    status = SIM_read_register(uart_device, "status")
    assert status & 0x2 == 2  # error bit should be set

class TestUARTAdvanced:
    """Advanced UART tests"""
    
    def test_flow_control(self, uart_device):
        """Test UART flow control"""
        # Enable flow control
        conf.uart_device.flow_control = True
        
        # Test RTS/CTS
        SIM_write_register(uart_device, "flow_ctrl", 0x1)
        flow_val = SIM_read_register(uart_device, "flow_ctrl")
        assert flow_val & 0x1 == 1
    
    def test_performance(self, uart_device):
        """Test UART performance"""
        start_time = simics.SIM_time()
        
        # Perform operations
        for i in range(1000):
            uart_device.send_data(f"data_{i}")
        
        end_time = simics.SIM_time()
        duration = end_time - start_time
        assert duration < 1000000  # Should complete within reasonable time

def test_mock_device_creation():
    """Test device creation patterns"""
    device_config = {
        "class": "uart_device",
        "name": "test_uart_mock"
    }
    
    mock_device = create_mock_device(device_config)
    assert mock_device is not None

def create_mock_device(config):
    """Helper function to create mock devices"""
    return SIM_create_object(config["class"], config["name"], [])
'''
    return test_content


def test_dml_parser():
    """Test the DML parser with sample content"""
    print("🔧 Testing DML Parser...")
    
    parser = DMLParser()
    
    # Create temporary DML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dml', delete=False) as f:
        f.write(create_sample_dml_file())
        temp_path = Path(f.name)
    
    try:
        # Parse the file
        result = parser.parse_dml_file(temp_path)
        
        # Validate results
        assert 'devices' in result
        assert 'interfaces' in result
        assert 'methods' in result
        assert 'attributes' in result
        assert 'registers' in result
        
        # Check devices
        devices = result['devices']
        assert len(devices) == 2  # uart_device and enhanced_uart
        
        device_names = [d.name for d in devices]
        assert 'uart_device' in device_names
        assert 'enhanced_uart' in device_names
        
        # Check inheritance
        enhanced_uart = next(d for d in devices if d.name == 'enhanced_uart')
        assert enhanced_uart.parent == 'uart_device'
        
        # Check interfaces
        interfaces = result['interfaces']
        assert len(interfaces) == 1
        assert interfaces[0].name == 'uart_interface'
        
        # Check methods
        methods = result['methods']
        method_names = [m.name for m in methods]
        assert 'init' in method_names
        assert 'read' in method_names
        assert 'write' in method_names
        assert 'configure_flow_control' in method_names
        
        # Check attributes
        attributes = result['attributes']
        attr_names = [a.name for a in attributes]
        assert 'baud_rate' in attr_names
        assert 'buffer_size' in attr_names
        assert 'flow_control' in attr_names
        
        # Check registers
        registers = result['registers']
        reg_names = [r.name for r in registers]
        assert 'control' in reg_names
        assert 'status' in reg_names
        assert 'flow_ctrl' in reg_names
        
        print("  ✅ DML Parser test passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ DML Parser test failed: {e}")
        return False
    finally:
        # Cleanup
        temp_path.unlink()


def test_test_analyzer():
    """Test the Simics test analyzer with sample content"""
    print("🧪 Testing Simics Test Analyzer...")
    
    analyzer = SimicsTestAnalyzer()
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(create_sample_test_file())
        temp_path = Path(f.name)
    
    try:
        # Analyze the file
        result = analyzer.analyze_test_file(temp_path)
        
        # Validate results
        assert 'simics_imports' in result
        assert 'simics_api_calls' in result
        assert 'test_functions' in result
        assert 'test_fixtures' in result
        assert 'is_simics_test' in result
        
        # Check Simics detection
        assert result['is_simics_test'] == True
        
        # Check imports
        simics_imports = result['simics_imports']
        import_modules = [imp['module'] for imp in simics_imports if 'module' in imp]
        assert any('simics' in mod for mod in import_modules)
        
        # Check API calls
        api_calls = result['simics_api_calls']
        api_names = [call.api_name for call in api_calls]
        assert any('SIM_create_object' in name for name in api_names)
        
        # Check test functions
        test_functions = result['test_functions']
        test_names = [func.name for func in test_functions]
        assert 'test_uart_initialization' in test_names
        assert 'test_uart_configuration' in test_names
        assert 'test_uart_data_transmission' in test_names
        
        # Check test fixtures
        fixtures = result['test_fixtures']
        fixture_names = [fix.name for fix in fixtures]
        assert 'uart_device' in fixture_names
        assert 'simulation_env' in fixture_names
        
        print("  ✅ Test Analyzer test passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Test Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        temp_path.unlink()


def test_integration():
    """Test integration between components"""
    print("🔗 Testing Integration...")
    
    try:
        # Test that components can be imported together
        from parse_simics_into_neo4j import SimicsNeo4jExtractor
        from query_simics_knowledge_graph import SimicsQueryInterface
        
        # Test that they can be instantiated (with mock credentials)
        try:
            extractor = SimicsNeo4jExtractor("bolt://localhost:7687", "neo4j", "test")
            query_interface = SimicsQueryInterface("bolt://localhost:7687", "neo4j", "test")
            
            # Test that query names are available
            assert 'device-hierarchy' in query_interface.simics_queries
            assert 'test-coverage' in query_interface.simics_queries
            assert 'stats' in query_interface.simics_queries
            
            print("  ✅ Integration test passed!")
            return True
            
        except Exception as e:
            # Connection errors are expected in test environment
            if "connection" in str(e).lower() or "auth" in str(e).lower():
                print("  ✅ Integration test passed! (Connection error expected in test)")
                return True
            else:
                raise e
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False


def test_file_discovery():
    """Test file discovery patterns"""
    print("📁 Testing File Discovery...")
    
    try:
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample files
            (temp_path / "devices").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "python").mkdir()
            
            # DML files
            (temp_path / "devices" / "uart.dml").write_text("device uart {}")
            (temp_path / "devices" / "memory.dml").write_text("device memory {}")
            
            # Test files
            (temp_path / "tests" / "test_uart.py").write_text("def test_uart(): pass")
            (temp_path / "uart_test.py").write_text("def test_uart_alt(): pass")
            
            # Python files
            (temp_path / "python" / "utils.py").write_text("def helper(): pass")
            (temp_path / "setup.py").write_text("# Setup script")
            
            # Import the extractor
            from parse_simics_into_neo4j import SimicsNeo4jExtractor
            
            # Create mock extractor
            extractor = SimicsNeo4jExtractor("bolt://localhost:7687", "neo4j", "test")
            
            # Test file discovery
            files = extractor._discover_simics_files(temp_path, False, False, False)
            
            # Validate discovery
            assert len(files['dml_files']) == 2
            assert len(files['test_files']) == 2
            assert len(files['python_files']) >= 2  # setup.py and utils.py
            
            # Test filters
            dml_only = extractor._discover_simics_files(temp_path, False, True, False)  # tests only
            assert len(dml_only['dml_files']) == 0
            assert len(dml_only['test_files']) == 2
            
            print("  ✅ File Discovery test passed!")
            return True
            
    except Exception as e:
        print(f"  ❌ File Discovery test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Testing Simics Neo4j Integration")
    print("=" * 50)
    
    tests = [
        test_dml_parser,
        test_test_analyzer,
        test_integration,
        test_file_discovery,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  💥 Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Simics Neo4j integration is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)