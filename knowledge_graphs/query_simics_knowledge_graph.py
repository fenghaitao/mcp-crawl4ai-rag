"""
Simics Knowledge Graph Query Interface

This module provides pre-built queries and an interactive interface for exploring
the Simics code knowledge graph in Neo4j.

Usage:
    python query_simics_knowledge_graph.py --query device-hierarchy
    python query_simics_knowledge_graph.py --query test-coverage
    python query_simics_knowledge_graph.py --interactive
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from query_knowledge_graph import KnowledgeGraphQuerier


class SimicsQueryInterface(KnowledgeGraphQuerier):
    """Extended query interface for Simics-specific analysis"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        super().__init__(neo4j_uri, neo4j_user, neo4j_password)
        
        # Pre-defined Simics queries
        self.simics_queries = {
            'device-hierarchy': self._query_device_hierarchy,
            'device-interfaces': self._query_device_interfaces,
            'device-methods': self._query_device_methods,
            'device-registers': self._query_device_registers,
            'test-coverage': self._query_test_coverage,
            'untested-devices': self._query_untested_devices,
            'api-usage': self._query_api_usage,
            'test-patterns': self._query_test_patterns,
            'device-dependencies': self._query_device_dependencies,
            'cross-language-links': self._query_cross_language_links,
            'similar-devices': self._query_similar_devices,
            'test-fixtures': self._query_test_fixtures,
            'stats': self._query_stats,
        }
    
    async def run_query(self, cypher: str, params: Dict = None) -> List[Dict[str, Any]]:
        """Helper method to run Cypher queries"""
        if self.driver is None:
            await self.initialize()
        async with self.driver.session() as session:
            result = await session.run(cypher, params or {})
            records = []
            async for record in result:
                records.append(dict(record))
            return records
    
    async def run_simics_query(self, query_name: str, **kwargs) -> List[Dict[str, Any]]:
        """Run a pre-defined Simics query"""
        if query_name not in self.simics_queries:
            available = ', '.join(self.simics_queries.keys())
            raise ValueError(f"Unknown query '{query_name}'. Available: {available}")
        
        query_func = self.simics_queries[query_name]
        return await query_func(**kwargs)
    
    async def _query_device_hierarchy(self, device_name: str = None) -> List[Dict[str, Any]]:
        """Query device inheritance hierarchy"""
        if device_name:
            cypher = """
            MATCH path = (child:DMLDevice)-[:INHERITS_FROM*]->(ancestor:DMLDevice)
            WHERE child.name = $device_name OR ancestor.name = $device_name
            RETURN path,
                   [node in nodes(path) | {name: node.name, file_path: node.file_path}] as hierarchy
            ORDER BY length(path) DESC
            """
            params = {"device_name": device_name}
        else:
            cypher = """
            MATCH path = (child:DMLDevice)-[:INHERITS_FROM*]->(parent:DMLDevice)
            RETURN path,
                   [node in nodes(path) | {name: node.name, file_path: node.file_path}] as hierarchy
            ORDER BY length(path) DESC
            LIMIT 50
            """
            params = {}
        
        return await self.run_query(cypher, params)
    
    async def _query_device_interfaces(self, device_name: str = None) -> List[Dict[str, Any]]:
        """Query device interface implementations"""
        if device_name:
            cypher = """
            MATCH (d:DMLDevice {name: $device_name})-[:IMPLEMENTS]->(i:DMLInterface)
            RETURN d.name as device_name, d.file_path as device_file,
                   i.name as interface_name, i.file_path as interface_file
            """
            params = {"device_name": device_name}
        else:
            cypher = """
            MATCH (d:DMLDevice)-[:IMPLEMENTS]->(i:DMLInterface)
            RETURN d.name as device_name, d.file_path as device_file,
                   i.name as interface_name, i.file_path as interface_file,
                   count(*) as implementation_count
            ORDER BY implementation_count DESC
            """
            params = {}
        
        return await self.run_query(cypher, params)
    
    async def _query_device_methods(self, device_name: str) -> List[Dict[str, Any]]:
        """Query methods for a specific device"""
        cypher = """
        MATCH (d:DMLDevice {name: $device_name})-[:HAS_METHOD]->(m:DMLMethod)
        RETURN m.name as method_name, m.parameters as parameters, 
               m.return_type as return_type, m.line_number as line_number
        ORDER BY m.line_number
        """
        return await self.run_query(cypher, {"device_name": device_name})
    
    async def _query_device_registers(self, device_name: str) -> List[Dict[str, Any]]:
        """Query registers for a specific device"""
        cypher = """
        MATCH (d:DMLDevice {name: $device_name})-[:HAS_REGISTER]->(r:DMLRegister)
        RETURN r.name as register_name, r.address as address, 
               r.size as size, r.line_number as line_number
        ORDER BY r.address
        """
        return await self.run_query(cypher, {"device_name": device_name})
    
    async def _query_test_coverage(self, device_name: str = None) -> List[Dict[str, Any]]:
        """Query test coverage for devices"""
        if device_name:
            cypher = """
            MATCH (d:DMLDevice {name: $device_name})
            OPTIONAL MATCH (t:TestFunction)-[:TESTS]->(d)
            RETURN d.name as device_name, d.file_path as device_file,
                   collect(t.name) as test_functions,
                   count(t) as test_count
            """
            params = {"device_name": device_name}
        else:
            cypher = """
            MATCH (d:DMLDevice)
            OPTIONAL MATCH (t:TestFunction)-[:TESTS]->(d)
            RETURN d.name as device_name, d.file_path as device_file,
                   collect(t.name) as test_functions,
                   count(t) as test_count
            ORDER BY test_count DESC
            """
            params = {}
        
        return await self.run_query(cypher, params)
    
    async def _query_untested_devices(self) -> List[Dict[str, Any]]:
        """Find devices without test coverage"""
        cypher = """
        MATCH (d:DMLDevice)
        WHERE NOT EXISTS((d)<-[:TESTS]-(:TestFunction))
        RETURN d.name as device_name, d.file_path as device_file
        ORDER BY d.name
        """
        return await self.run_query(cypher)
    
    async def _query_api_usage(self, api_name: str = None) -> List[Dict[str, Any]]:
        """Query Simics API usage patterns"""
        if api_name:
            cypher = """
            MATCH (api:SimicsAPI {name: $api_name})<-[:USES_API]-(t:TestFunction)
            RETURN api.name as api_name, api.module as api_module,
                   t.name as test_function, t.file_path as test_file
            """
            params = {"api_name": api_name}
        else:
            cypher = """
            MATCH (api:SimicsAPI)<-[:USES_API]-(t:TestFunction)
            RETURN api.name as api_name, api.module as api_module,
                   count(t) as usage_count,
                   collect(DISTINCT t.file_path)[0..5] as sample_test_files
            ORDER BY usage_count DESC
            LIMIT 20
            """
            params = {}
        
        return await self.run_query(cypher, params)
    
    async def _query_test_patterns(self) -> List[Dict[str, Any]]:
        """Analyze test patterns and categories"""
        cypher = """
        MATCH (f:TestFile)-[:CONTAINS]->(t:TestFunction)
        RETURN f.file_path as test_file,
               count(t) as test_function_count,
               collect(t.name)[0..5] as sample_functions,
               f.is_simics_test as is_simics_test
        ORDER BY test_function_count DESC
        """
        return await self.run_query(cypher)
    
    async def _query_device_dependencies(self, device_name: str) -> List[Dict[str, Any]]:
        """Query device dependencies and relationships"""
        cypher = """
        MATCH (d:DMLDevice {name: $device_name})
        OPTIONAL MATCH (d)-[:INHERITS_FROM]->(parent:DMLDevice)
        OPTIONAL MATCH (child:DMLDevice)-[:INHERITS_FROM]->(d)
        OPTIONAL MATCH (d)-[:IMPLEMENTS]->(i:DMLInterface)
        OPTIONAL MATCH (t:TestFunction)-[:TESTS]->(d)
        RETURN d.name as device_name,
               parent.name as parent_device,
               collect(DISTINCT child.name) as child_devices,
               collect(DISTINCT i.name) as interfaces,
               collect(DISTINCT t.name) as test_functions
        """
        return await self.run_query(cypher, {"device_name": device_name})
    
    async def _query_cross_language_links(self) -> List[Dict[str, Any]]:
        """Find connections between DML devices and Python tests"""
        cypher = """
        MATCH (dml:DMLFile)-[:DEFINES]->(d:DMLDevice)
        MATCH (test:TestFile)-[:CONTAINS]->(t:TestFunction)-[:TESTS]->(d)
        RETURN d.name as device_name,
               dml.file_path as dml_file,
               test.file_path as test_file,
               t.name as test_function
        ORDER BY d.name
        """
        return await self.run_query(cypher)
    
    async def _query_similar_devices(self, device_name: str) -> List[Dict[str, Any]]:
        """Find devices similar to the given device"""
        cypher = """
        MATCH (d1:DMLDevice {name: $device_name})-[:HAS_METHOD]->(m1:DMLMethod)
        MATCH (d2:DMLDevice)-[:HAS_METHOD]->(m2:DMLMethod)
        WHERE d1 <> d2 AND m1.name = m2.name
        RETURN d2.name as similar_device,
               d2.file_path as device_file,
               count(m2) as common_methods,
               collect(m2.name)[0..5] as sample_common_methods
        ORDER BY common_methods DESC
        LIMIT 10
        """
        return await self.run_query(cypher, {"device_name": device_name})
    
    async def _query_test_fixtures(self) -> List[Dict[str, Any]]:
        """Query test fixtures and their usage"""
        cypher = """
        MATCH (f:TestFile)-[:CONTAINS]->(fx:TestFixture)
        RETURN fx.name as fixture_name,
               fx.scope as scope,
               fx.dependencies as dependencies,
               f.file_path as test_file,
               fx.line_number as line_number
        ORDER BY fx.scope, fx.name
        """
        return await self.run_query(cypher)
    
    async def _query_stats(self) -> List[Dict[str, Any]]:
        """Get overall statistics about the Simics codebase"""
        cypher = """
        CALL {
            MATCH (d:DMLDevice) RETURN count(d) as dml_devices
        }
        CALL {
            MATCH (i:DMLInterface) RETURN count(i) as dml_interfaces
        }
        CALL {
            MATCH (m:DMLMethod) RETURN count(m) as dml_methods
        }
        CALL {
            MATCH (r:DMLRegister) RETURN count(r) as dml_registers
        }
        CALL {
            MATCH (t:TestFunction) RETURN count(t) as test_functions
        }
        CALL {
            MATCH (f:TestFile) WHERE f.is_simics_test = true RETURN count(f) as simics_test_files
        }
        CALL {
            MATCH (api:SimicsAPI) RETURN count(api) as simics_apis
        }
        CALL {
            MATCH (d:DMLDevice)<-[:TESTS]-(t:TestFunction) RETURN count(DISTINCT d) as tested_devices
        }
        CALL {
            MATCH (d:DMLDevice) WHERE NOT EXISTS((d)<-[:TESTS]-(:TestFunction)) RETURN count(d) as untested_devices
        }
        RETURN dml_devices, dml_interfaces, dml_methods, dml_registers,
               test_functions, simics_test_files, simics_apis,
               tested_devices, untested_devices
        """
        return await self.run_query(cypher)
    
    async def interactive_mode(self):
        """Interactive query mode for exploring Simics codebase"""
        print("🔍 Simics Knowledge Graph Interactive Mode")
        print("Type 'help' for available commands, 'quit' to exit")
        print()
        
        while True:
            try:
                command = input("simics-kg> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                elif command.lower() == 'help':
                    self._show_help()
                elif command.lower() == 'list':
                    self._list_queries()
                elif command.lower() == 'stats':
                    await self._show_stats()
                elif command.startswith('query '):
                    await self._handle_query_command(command[6:])
                elif command.startswith('custom '):
                    await self._handle_custom_query(command[7:])
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self):
        """Show help for interactive mode"""
        help_text = """
Available commands:
  help                    - Show this help message
  list                    - List all available pre-defined queries
  stats                   - Show overall codebase statistics
  query <name> [args]     - Run a pre-defined query
  custom <cypher>         - Run a custom Cypher query
  quit                    - Exit interactive mode

Examples:
  query device-hierarchy uart_device
  query test-coverage
  query api-usage SIM_create_object
  custom MATCH (d:DMLDevice) RETURN d.name LIMIT 5
        """
        print(help_text)
    
    def _list_queries(self):
        """List all available pre-defined queries"""
        print("Available pre-defined queries:")
        for query_name in sorted(self.simics_queries.keys()):
            print(f"  - {query_name}")
        print()
    
    async def _show_stats(self):
        """Show codebase statistics"""
        try:
            results = await self._query_stats()
            if results:
                stats = results[0]
                print("📊 Simics Codebase Statistics:")
                print(f"  DML Devices: {stats['dml_devices']}")
                print(f"  DML Interfaces: {stats['dml_interfaces']}")
                print(f"  DML Methods: {stats['dml_methods']}")
                print(f"  DML Registers: {stats['dml_registers']}")
                print(f"  Test Functions: {stats['test_functions']}")
                print(f"  Simics Test Files: {stats['simics_test_files']}")
                print(f"  Simics APIs: {stats['simics_apis']}")
                print(f"  Tested Devices: {stats['tested_devices']}")
                print(f"  Untested Devices: {stats['untested_devices']}")
                
                if stats['dml_devices'] > 0:
                    coverage = (stats['tested_devices'] / stats['dml_devices']) * 100
                    print(f"  Test Coverage: {coverage:.1f}%")
                print()
        except Exception as e:
            print(f"Error getting stats: {e}")
    
    async def _handle_query_command(self, command: str):
        """Handle query command with arguments"""
        parts = command.split()
        if not parts:
            print("Query name required. Use 'list' to see available queries.")
            return
        
        query_name = parts[0]
        args = parts[1:]
        
        if query_name not in self.simics_queries:
            print(f"Unknown query '{query_name}'. Use 'list' to see available queries.")
            return
        
        try:
            # Parse arguments based on query type
            kwargs = {}
            if args:
                if query_name in ['device-hierarchy', 'device-methods', 'device-registers', 
                                'test-coverage', 'device-dependencies', 'similar-devices']:
                    kwargs['device_name'] = args[0]
                elif query_name == 'api-usage':
                    kwargs['api_name'] = args[0]
            
            results = await self.run_simics_query(query_name, **kwargs)
            self._display_results(results, query_name)
            
        except Exception as e:
            print(f"Error running query: {e}")
    
    async def _handle_custom_query(self, cypher: str):
        """Handle custom Cypher query"""
        try:
            results = await self.run_query(cypher)
            self._display_results(results, "custom")
        except Exception as e:
            print(f"Error running custom query: {e}")
    
    def _display_results(self, results: List[Dict[str, Any]], query_name: str):
        """Display query results in a formatted way"""
        if not results:
            print("No results found.")
            return
        
        print(f"📋 Results ({len(results)} records):")
        
        # Limit output for readability
        display_results = results[:20] if len(results) > 20 else results
        
        for i, result in enumerate(display_results, 1):
            print(f"\n{i}. ", end="")
            if query_name == 'device-hierarchy':
                hierarchy = result.get('hierarchy', [])
                hierarchy_str = " → ".join(node['name'] for node in hierarchy)
                print(f"Hierarchy: {hierarchy_str}")
            elif query_name == 'test-coverage':
                device = result['device_name']
                test_count = result['test_count']
                print(f"Device: {device} (Tests: {test_count})")
                if result['test_functions']:
                    tests = ", ".join(result['test_functions'][:3])
                    if len(result['test_functions']) > 3:
                        tests += f" (and {len(result['test_functions']) - 3} more)"
                    print(f"   Test functions: {tests}")
            else:
                # Generic display
                for key, value in result.items():
                    if isinstance(value, list) and len(value) > 5:
                        value = value[:5] + [f"... ({len(value) - 5} more)"]
                    print(f"{key}: {value}")
        
        if len(results) > 20:
            print(f"\n... and {len(results) - 20} more results")
        print()


async def main():
    """Main entry point for Simics knowledge graph queries"""
    parser = argparse.ArgumentParser(
        description="Query Simics knowledge graph in Neo4j",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available queries:
  device-hierarchy [device_name]  - Show device inheritance hierarchy
  device-interfaces [device_name] - Show interface implementations  
  device-methods <device_name>    - Show methods for a device
  device-registers <device_name>  - Show registers for a device
  test-coverage [device_name]     - Show test coverage for devices
  untested-devices               - Find devices without tests
  api-usage [api_name]           - Show Simics API usage patterns
  test-patterns                  - Analyze test patterns
  device-dependencies <device>   - Show device relationships
  cross-language-links           - Find DML-Python connections
  similar-devices <device_name>  - Find similar devices
  test-fixtures                  - Show test fixtures
  stats                         - Show codebase statistics

Examples:
  python query_simics_knowledge_graph.py --query stats
  python query_simics_knowledge_graph.py --query device-hierarchy uart_device
  python query_simics_knowledge_graph.py --query test-coverage
  python query_simics_knowledge_graph.py --interactive
        """
    )
    
    # Query options
    parser.add_argument('--query', help='Pre-defined query to run')
    parser.add_argument('--args', nargs='*', help='Arguments for the query')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--custom', help='Custom Cypher query to run')
    
    # Neo4j connection
    parser.add_argument('--neo4j-uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--neo4j-user', default='neo4j', help='Neo4j username')
    parser.add_argument('--neo4j-password', help='Neo4j password (or set NEO4J_PASSWORD env var)')
    
    # Output options
    parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
    parser.add_argument('--limit', type=int, default=50, help='Limit number of results')
    
    args = parser.parse_args()
    
    # Get Neo4j password
    neo4j_password = args.neo4j_password or os.getenv('NEO4J_PASSWORD')
    if not neo4j_password:
        print("Error: Neo4j password must be provided via --neo4j-password or NEO4J_PASSWORD env var")
        sys.exit(1)
    
    try:
        # Initialize query interface
        query_interface = SimicsQueryInterface(args.neo4j_uri, args.neo4j_user, neo4j_password)
        
        if args.interactive:
            await query_interface.interactive_mode()
        elif args.query:
            # Run pre-defined query
            kwargs = {}
            if args.args:
                # Simple argument parsing - could be enhanced
                if args.query in ['device-hierarchy', 'device-methods', 'device-registers', 
                                'test-coverage', 'device-dependencies', 'similar-devices']:
                    kwargs['device_name'] = args.args[0]
                elif args.query == 'api-usage':
                    kwargs['api_name'] = args.args[0]
            
            results = await query_interface.run_simics_query(args.query, **kwargs)
            
            if args.format == 'json':
                print(json.dumps(results, indent=2))
            else:
                query_interface._display_results(results, args.query)
                
        elif args.custom:
            # Run custom query
            results = await query_interface.run_query(args.custom)
            
            if args.format == 'json':
                print(json.dumps(results, indent=2))
            else:
                query_interface._display_results(results, "custom")
        else:
            print("Error: One of --query, --custom, or --interactive must be specified")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())