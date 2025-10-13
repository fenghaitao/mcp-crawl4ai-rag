"""
Simics Neo4j Integration

This script extends the existing Neo4j code analysis to support Simics-specific files:
- DML (Device Modeling Language) files
- Python test files with Simics-specific patterns
- Local directory analysis (not just git repositories)

Usage:
    python parse_simics_into_neo4j.py --local-path /path/to/simics-installation/
    python parse_simics_into_neo4j.py --local-path /path/to/simics/ --dml-only
    python parse_simics_into_neo4j.py --local-path /path/to/simics/ --tests-only
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from dataclasses import asdict

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from parse_repo_into_neo4j import DirectNeo4jExtractor, Neo4jCodeAnalyzer
from simics_dml_parser import DMLParser
from simics_test_analyzer import SimicsTestAnalyzer


class SimicsNeo4jExtractor(DirectNeo4jExtractor):
    """Extended Neo4j extractor for Simics code analysis"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        super().__init__(neo4j_uri, neo4j_user, neo4j_password)
        self.dml_parser = DMLParser()
        self.test_analyzer = SimicsTestAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # File patterns for Simics
        self.simics_patterns = {
            'dml_files': ['*.dml'],
            'test_files': ['test_*.py', '*_test.py', 'tests/*.py'],
            'python_files': ['*.py'],
        }
    
    async def analyze_local_directory(self, directory_path: str, 
                                    dml_only: bool = False, 
                                    tests_only: bool = False,
                                    python_only: bool = False) -> bool:
        """
        Analyze a local Simics directory
        
        Args:
            directory_path: Path to local Simics directory
            dml_only: Only analyze DML files
            tests_only: Only analyze test files
            python_only: Only analyze regular Python files
            
        Returns:
            True if analysis completed successfully
        """
        try:
            directory = Path(directory_path)
            if not directory.exists():
                self.logger.error(f"Directory not found: {directory_path}")
                return False
            
            self.logger.info(f"🚀 Starting Simics analysis of: {directory_path}")
            
            # Discover files
            files = self._discover_simics_files(directory, dml_only, tests_only, python_only)
            
            total_files = sum(len(file_list) for file_list in files.values())
            if total_files == 0:
                self.logger.warning("No relevant files found for analysis")
                return False
            
            self.logger.info(f"📁 Found {total_files} files to analyze:")
            self.logger.info(f"   DML files: {len(files['dml_files'])}")
            self.logger.info(f"   Test files: {len(files['test_files'])}")
            self.logger.info(f"   Python files: {len(files['python_files'])}")
            
            # Initialize Neo4j connection if not already done
            if self.driver is None:
                await self.initialize()
            
            # Setup Neo4j constraints and indexes
            await self._setup_simics_schema()
            
            # Analyze files by type
            analysis_results = {}
            
            if files['dml_files'] and not tests_only and not python_only:
                self.logger.info("🔧 Analyzing DML files...")
                analysis_results['dml'] = await self._analyze_dml_files(files['dml_files'], directory)
            
            if files['test_files'] and not dml_only and not python_only:
                self.logger.info("🧪 Analyzing test files...")
                analysis_results['tests'] = await self._analyze_test_files(files['test_files'], directory)
            
            if files['python_files'] and not dml_only and not tests_only:
                self.logger.info("🐍 Analyzing Python files...")
                analysis_results['python'] = await self._analyze_python_files(files['python_files'], directory)
            
            # Create relationships between analyzed elements
            await self._create_simics_relationships(analysis_results)
            
            # Log summary
            total_processed = sum(len(results) for results in analysis_results.values())
            self.logger.info(f"✅ Successfully analyzed {total_processed} files")
            self.logger.info("🎉 Simics Neo4j analysis complete!")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error analyzing directory {directory_path}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _discover_simics_files(self, directory: Path, dml_only: bool, 
                              tests_only: bool, python_only: bool) -> Dict[str, List[Path]]:
        """Discover Simics-related files in the directory"""
        files = {
            'dml_files': [],
            'test_files': [],
            'python_files': []
        }
        
        self.logger.info(f"🔍 Discovering files in: {directory}")
        
        # Find DML files
        if not tests_only and not python_only:
            for pattern in self.simics_patterns['dml_files']:
                files['dml_files'].extend(directory.rglob(pattern))
        
        # Find test files
        if not dml_only and not python_only:
            test_files = set()
            for pattern in self.simics_patterns['test_files']:
                test_files.update(directory.rglob(pattern))
            files['test_files'] = list(test_files)
        
        # Find regular Python files (excluding tests)
        if not dml_only and not tests_only:
            all_python = set(directory.rglob('*.py'))
            test_files_set = set(files['test_files'])
            
            # Filter out test files and common non-source directories
            excluded_dirs = {'__pycache__', '.git', '.tox', 'build', 'dist'}
            python_files = []
            
            for py_file in all_python:
                # Skip if it's a test file
                if py_file in test_files_set:
                    continue
                
                # Skip if it's in an excluded directory
                if any(excluded_dir in str(py_file) for excluded_dir in excluded_dirs):
                    continue
                
                # Skip if it's a test file by name pattern
                if (py_file.name.startswith('test_') or 
                    py_file.name.endswith('_test.py') or
                    'test' in str(py_file.parent)):
                    continue
                
                python_files.append(py_file)
            
            files['python_files'] = python_files
        
        return files
    
    async def _setup_simics_schema(self):
        """Setup Neo4j constraints and indexes for Simics node types"""
        try:
            constraints = [
                # DML node constraints
                "CREATE CONSTRAINT dml_device_name IF NOT EXISTS FOR (d:DMLDevice) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT dml_interface_name IF NOT EXISTS FOR (i:DMLInterface) REQUIRE i.name IS UNIQUE",
                "CREATE CONSTRAINT dml_file_path IF NOT EXISTS FOR (f:DMLFile) REQUIRE f.file_path IS UNIQUE",
                
                # Test node constraints
                "CREATE CONSTRAINT test_function_id IF NOT EXISTS FOR (t:TestFunction) REQUIRE (t.name, t.file_path) IS UNIQUE",
                "CREATE CONSTRAINT test_fixture_id IF NOT EXISTS FOR (f:TestFixture) REQUIRE (f.name, f.file_path) IS UNIQUE",
                
                # API and device constraints
                "CREATE CONSTRAINT simics_api_name IF NOT EXISTS FOR (a:SimicsAPI) REQUIRE a.name IS UNIQUE",
                "CREATE CONSTRAINT device_under_test_name IF NOT EXISTS FOR (d:DeviceUnderTest) REQUIRE d.name IS UNIQUE",
            ]
            
            indexes = [
                # Performance indexes
                "CREATE INDEX dml_method_name IF NOT EXISTS FOR (m:DMLMethod) ON (m.name)",
                "CREATE INDEX dml_attribute_name IF NOT EXISTS FOR (a:DMLAttribute) ON (a.name)",
                "CREATE INDEX test_category IF NOT EXISTS FOR (t:TestFunction) ON (t.category)",
                "CREATE INDEX simics_api_module IF NOT EXISTS FOR (a:SimicsAPI) ON (a.module)",
            ]
            
            for constraint in constraints:
                try:
                    await self.driver.execute_query(constraint)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        self.logger.warning(f"Could not create constraint: {e}")
            
            for index in indexes:
                try:
                    await self.driver.execute_query(index)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        self.logger.warning(f"Could not create index: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error setting up Simics schema: {e}")
    
    async def _analyze_dml_files(self, dml_files: List[Path], base_path: Path) -> List[Dict[str, Any]]:
        """Analyze DML files and create Neo4j nodes"""
        results = []
        
        for i, dml_file in enumerate(dml_files, 1):
            self.logger.info(f"  📄 [{i}/{len(dml_files)}] Processing: {dml_file.name}")
            
            try:
                # Parse DML file
                analysis = self.dml_parser.parse_dml_file(dml_file, base_path)
                
                if 'error' in analysis:
                    self.logger.warning(f"    ⚠️  Error parsing {dml_file.name}: {analysis['error']}")
                    continue
                
                # Create Neo4j nodes for DML elements
                await self._create_dml_nodes(analysis)
                
                results.append(analysis)
                self.logger.info(f"    ✅ {len(analysis['devices'])} devices, {len(analysis['methods'])} methods")
                
            except Exception as e:
                self.logger.error(f"    ❌ Error processing {dml_file.name}: {e}")
        
        return results
    
    async def _analyze_test_files(self, test_files: List[Path], base_path: Path) -> List[Dict[str, Any]]:
        """Analyze test files and create Neo4j nodes"""
        results = []
        
        # Create project modules set for analysis
        project_modules = set()
        
        for i, test_file in enumerate(test_files, 1):
            self.logger.info(f"  🧪 [{i}/{len(test_files)}] Processing: {test_file.name}")
            
            try:
                # Analyze test file
                analysis = self.test_analyzer.analyze_test_file(test_file, base_path, project_modules)
                
                if 'error' in analysis:
                    self.logger.warning(f"    ⚠️  Error analyzing {test_file.name}: {analysis['error']}")
                    continue
                
                # Create Neo4j nodes for test elements
                await self._create_test_nodes(analysis)
                
                results.append(analysis)
                self.logger.info(f"    ✅ {len(analysis['test_functions'])} tests, {len(analysis['simics_api_calls'])} API calls")
                
            except Exception as e:
                self.logger.error(f"    ❌ Error processing {test_file.name}: {e}")
        
        return results
    
    async def _analyze_python_files(self, python_files: List[Path], base_path: Path) -> List[Dict[str, Any]]:
        """Analyze regular Python files using existing analyzer"""
        results = []
        
        # Create project modules set
        project_modules = set()
        
        analyzer = Neo4jCodeAnalyzer()
        
        for i, py_file in enumerate(python_files, 1):
            self.logger.info(f"  🐍 [{i}/{len(python_files)}] Processing: {py_file.name}")
            
            try:
                # Use existing Python analyzer
                analysis = analyzer.analyze_python_file(py_file, base_path, project_modules)
                
                if 'error' in analysis:
                    self.logger.warning(f"    ⚠️  Error analyzing {py_file.name}: {analysis['error']}")
                    continue
                
                # Create Neo4j nodes using existing method
                await self._create_python_nodes(analysis)
                
                results.append(analysis)
                self.logger.info(f"    ✅ {len(analysis.get('classes', []))} classes, {len(analysis.get('functions', []))} functions")
                
            except Exception as e:
                self.logger.error(f"    ❌ Error processing {py_file.name}: {e}")
        
        return results
    
    async def _create_dml_nodes(self, analysis: Dict[str, Any]):
        """Create Neo4j nodes for DML analysis results"""
        file_path = analysis['file_path']
        
        # Create DML file node
        await self.driver.execute_query("""
            MERGE (f:File:DMLFile {file_path: $file_path})
            SET f.file_type = 'dml',
                f.content_length = $content_length,
                f.line_count = $line_count
        """, file_path=file_path, 
             content_length=analysis.get('content_length', 0),
             line_count=analysis.get('line_count', 0))
        
        # Create device nodes
        for device in analysis['devices']:
            await self.driver.execute_query("""
                MERGE (d:DMLDevice {name: $name})
                SET d.file_path = $file_path,
                    d.line_number = $line_number,
                    d.parent = $parent
                WITH d
                MATCH (f:DMLFile {file_path: $file_path})
                MERGE (f)-[:DEFINES]->(d)
            """, name=device.name, file_path=file_path, 
                 line_number=device.line_number, parent=device.parent)
            
            # Create inheritance relationships
            if device.parent:
                await self.driver.execute_query("""
                    MATCH (child:DMLDevice {name: $child_name})
                    MATCH (parent:DMLDevice {name: $parent_name})
                    MERGE (child)-[:INHERITS_FROM]->(parent)
                """, child_name=device.name, parent_name=device.parent)
        
        # Create interface nodes
        for interface in analysis['interfaces']:
            await self.driver.execute_query("""
                MERGE (i:DMLInterface {name: $name})
                SET i.file_path = $file_path,
                    i.line_number = $line_number
                WITH i
                MATCH (f:DMLFile {file_path: $file_path})
                MERGE (f)-[:DEFINES]->(i)
            """, name=interface.name, file_path=file_path, 
                 line_number=interface.line_number)
        
        # Create method nodes
        for method in analysis['methods']:
            await self.driver.execute_query("""
                MERGE (m:DMLMethod {name: $name, device: $device, file_path: $file_path})
                SET m.line_number = $line_number,
                    m.parameters = $parameters,
                    m.return_type = $return_type
                WITH m
                MATCH (d:DMLDevice {name: $device})
                MERGE (d)-[:HAS_METHOD]->(m)
            """, name=method.name, device=method.device, file_path=file_path,
                 line_number=method.line_number, parameters=method.parameters,
                 return_type=method.return_type)
        
        # Create attribute nodes
        for attr in analysis['attributes']:
            await self.driver.execute_query("""
                MERGE (a:DMLAttribute {name: $name, device: $device, file_path: $file_path})
                SET a.line_number = $line_number,
                    a.type_name = $type_name
                WITH a
                MATCH (d:DMLDevice {name: $device})
                MERGE (d)-[:HAS_ATTRIBUTE]->(a)
            """, name=attr.name, device=attr.device, file_path=file_path,
                 line_number=attr.line_number, type_name=attr.type_name)
        
        # Create register nodes
        for register in analysis['registers']:
            await self.driver.execute_query("""
                MERGE (r:DMLRegister {name: $name, device: $device, file_path: $file_path})
                SET r.line_number = $line_number,
                    r.address = $address,
                    r.size = $size
                WITH r
                MATCH (d:DMLDevice {name: $device})
                MERGE (d)-[:HAS_REGISTER]->(r)
            """, name=register.name, device=register.device, file_path=file_path,
                 line_number=register.line_number, address=register.address,
                 size=register.size)
    
    async def _create_test_nodes(self, analysis: Dict[str, Any]):
        """Create Neo4j nodes for test analysis results"""
        file_path = analysis['file_path']
        
        # Create test file node
        await self.driver.execute_query("""
            MERGE (f:File:TestFile {file_path: $file_path})
            SET f.file_type = 'test',
                f.is_simics_test = $is_simics_test
        """, file_path=file_path, is_simics_test=analysis.get('is_simics_test', False))
        
        # Create Simics API nodes
        api_names = set()
        for api_call in analysis['simics_api_calls']:
            api_names.add(api_call.api_name)
        
        for api_name in api_names:
            await self.driver.execute_query("""
                MERGE (api:SimicsAPI {name: $name})
                SET api.module = $module
            """, name=api_name, module=api_call.module)
        
        # Create test function nodes
        for test_func in analysis['test_functions']:
            await self.driver.execute_query("""
                MERGE (t:TestFunction {name: $name, file_path: $file_path})
                SET t.class_name = $class_name,
                    t.line_number = $line_number,
                    t.devices_tested = $devices_tested,
                    t.simics_apis_used = $simics_apis_used,
                    t.fixtures_used = $fixtures_used
                WITH t
                MATCH (f:TestFile {file_path: $file_path})
                MERGE (f)-[:CONTAINS]->(t)
            """, name=test_func.name, file_path=file_path,
                 class_name=test_func.class_name, line_number=test_func.line_number,
                 devices_tested=test_func.devices_tested, 
                 simics_apis_used=test_func.simics_apis_used,
                 fixtures_used=test_func.fixtures_used)
            
            # Create relationships to APIs used
            for api_name in test_func.simics_apis_used:
                await self.driver.execute_query("""
                    MATCH (t:TestFunction {name: $test_name, file_path: $file_path})
                    MATCH (api:SimicsAPI {name: $api_name})
                    MERGE (t)-[:USES_API]->(api)
                """, test_name=test_func.name, file_path=file_path, api_name=api_name)
        
        # Create device under test nodes
        devices_under_test = set()
        for device_inst in analysis['device_instantiations']:
            devices_under_test.add(device_inst.device_type)
        
        for device_type in devices_under_test:
            await self.driver.execute_query("""
                MERGE (d:DeviceUnderTest {name: $name})
            """, name=device_type)
        
        # Create test fixture nodes
        for fixture in analysis['test_fixtures']:
            await self.driver.execute_query("""
                MERGE (fx:TestFixture {name: $name, file_path: $file_path})
                SET fx.scope = $scope,
                    fx.line_number = $line_number,
                    fx.dependencies = $dependencies
                WITH fx
                MATCH (f:TestFile {file_path: $file_path})
                MERGE (f)-[:CONTAINS]->(fx)
            """, name=fixture.name, file_path=file_path, scope=fixture.scope,
                 line_number=fixture.line_number, dependencies=fixture.dependencies)
    
    async def _create_python_nodes(self, analysis: Dict[str, Any]):
        """Create Neo4j nodes for regular Python files using existing logic"""
        # Reuse the existing create_nodes method from the parent class
        await self.create_nodes(analysis)
    
    async def _create_simics_relationships(self, analysis_results: Dict[str, List[Dict[str, Any]]]):
        """Create relationships between different Simics elements"""
        try:
            # Create relationships between tests and DML devices
            if 'tests' in analysis_results and 'dml' in analysis_results:
                await self._link_tests_to_dml_devices(analysis_results['tests'], analysis_results['dml'])
            
            # Create relationships between Python code and DML devices
            if 'python' in analysis_results and 'dml' in analysis_results:
                await self._link_python_to_dml_devices(analysis_results['python'], analysis_results['dml'])
            
            # Create relationships between tests and Python code
            if 'tests' in analysis_results and 'python' in analysis_results:
                await self._link_tests_to_python_code(analysis_results['tests'], analysis_results['python'])
                
        except Exception as e:
            self.logger.error(f"Error creating Simics relationships: {e}")
    
    async def _link_tests_to_dml_devices(self, test_results: List[Dict[str, Any]], 
                                       dml_results: List[Dict[str, Any]]):
        """Create relationships between test functions and DML devices they test"""
        # Extract device names from DML results
        dml_devices = set()
        for dml_analysis in dml_results:
            for device in dml_analysis['devices']:
                dml_devices.add(device.name)
        
        # Link test functions to devices they test
        for test_analysis in test_results:
            for test_func in test_analysis['test_functions']:
                for device_name in test_func.devices_tested:
                    # Try to match with actual DML devices (fuzzy matching)
                    for dml_device in dml_devices:
                        if (device_name.lower() in dml_device.lower() or 
                            dml_device.lower() in device_name.lower()):
                            
                            await self.driver.execute_query("""
                                MATCH (t:TestFunction {name: $test_name, file_path: $test_file})
                                MATCH (d:DMLDevice {name: $device_name})
                                MERGE (t)-[:TESTS]->(d)
                            """, test_name=test_func.name, test_file=test_analysis['file_path'],
                                 device_name=dml_device)
    
    async def _link_python_to_dml_devices(self, python_results: List[Dict[str, Any]], 
                                        dml_results: List[Dict[str, Any]]):
        """Create relationships between Python code and DML devices"""
        # This could be enhanced based on actual import patterns and usage
        pass
    
    async def _link_tests_to_python_code(self, test_results: List[Dict[str, Any]], 
                                       python_results: List[Dict[str, Any]]):
        """Create relationships between tests and the Python code they test"""
        # This could analyze import patterns to link tests to implementation
        pass


async def main():
    """Main entry point for Simics Neo4j analysis"""
    parser = argparse.ArgumentParser(
        description="Analyze Simics code into Neo4j knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze entire Simics installation
  python parse_simics_into_neo4j.py --local-path /path/to/simics-7-packages-2025-38-linux64/
  
  # Analyze only DML files
  python parse_simics_into_neo4j.py --local-path /path/to/simics/ --dml-only
  
  # Analyze only test files
  python parse_simics_into_neo4j.py --local-path /path/to/simics/ --tests-only
  
  # Analyze only regular Python files
  python parse_simics_into_neo4j.py --local-path /path/to/simics/ --python-only
        """
    )
    
    # Input options
    parser.add_argument('--local-path', help='Path to local Simics directory to analyze')
    parser.add_argument('--repo-url', help='Git repository URL (existing functionality)')
    
    # Analysis filter options
    parser.add_argument('--dml-only', action='store_true', help='Only analyze DML files')
    parser.add_argument('--tests-only', action='store_true', help='Only analyze test files')
    parser.add_argument('--python-only', action='store_true', help='Only analyze regular Python files')
    
    # Neo4j connection
    parser.add_argument('--neo4j-uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--neo4j-user', default='neo4j', help='Neo4j username')
    parser.add_argument('--neo4j-password', help='Neo4j password (or set NEO4J_PASSWORD env var)')
    
    # Logging
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get Neo4j password
    neo4j_password = args.neo4j_password or os.getenv('NEO4J_PASSWORD')
    if not neo4j_password:
        print("Error: Neo4j password must be provided via --neo4j-password or NEO4J_PASSWORD env var")
        sys.exit(1)
    
    # Validate input
    if not args.local_path and not args.repo_url:
        print("Error: Either --local-path or --repo-url must be provided")
        sys.exit(1)
    
    # Validate filter options
    filter_count = sum([args.dml_only, args.tests_only, args.python_only])
    if filter_count > 1:
        print("Error: Only one of --dml-only, --tests-only, --python-only can be specified")
        sys.exit(1)
    
    try:
        # Initialize extractor
        extractor = SimicsNeo4jExtractor(args.neo4j_uri, args.neo4j_user, neo4j_password)
        
        # Analyze based on input type
        if args.local_path:
            success = await extractor.analyze_local_directory(
                args.local_path, 
                dml_only=args.dml_only,
                tests_only=args.tests_only,
                python_only=args.python_only
            )
        else:
            # Use existing repository analysis functionality
            success = await extractor.analyze_repository(args.repo_url)
        
        if success:
            print("\n🎉 Analysis completed successfully!")
            print("You can now query the Neo4j database for Simics code insights.")
        else:
            print("\n❌ Analysis failed. Check the logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())