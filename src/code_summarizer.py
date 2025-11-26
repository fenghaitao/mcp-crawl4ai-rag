"""
Code summarization module for Simics source code.
Provides file-level and chunk-level summarization with domain-specific prompts.
"""
import os
from typing import Dict, Any, Optional
from iflow_client import create_chat_completion_iflow


# Simics-specific terminology and concepts
SIMICS_CONCEPTS = """
Simics is a full-system simulator for embedded systems and hardware development.
Key concepts:
- DML (Device Modeling Language): Domain-specific language for device models
- Devices: Hardware components (UART, SPI, I2C, timers, etc.)
- Registers: Memory-mapped hardware registers
- Banks: Groups of registers
- Fields: Bit fields within registers
- Methods: Device behavior implementations
- Attributes: Device configuration parameters
- Interfaces: Communication protocols between devices
- Events: Timed callbacks for simulation
- Templates: Reusable device patterns
"""


def generate_file_summary(
    content: str,
    metadata: Dict[str, Any],
    model: str = "iflow/qwen3-coder-plus",
    max_tokens: int = 200
) -> str:
    """
    Generate a high-level summary of an entire source file.
    
    Args:
        content: Full source code content
        metadata: File metadata (language, file_path, etc.)
        model: Model to use for summarization
        max_tokens: Maximum tokens for summary
        
    Returns:
        File-level summary string
    """
    language = metadata.get('language', 'unknown')
    file_path = metadata.get('file_path', 'unknown')
    device_name = metadata.get('device_name', '')
    
    # Truncate content for context (first 4000 chars)
    content_preview = content[:4000]
    if len(content) > 4000:
        content_preview += "\n... (truncated)"
    
    # Build Simics-specific prompt
    if language == 'dml':
        prompt = f"""You are analyzing a Simics DML (Device Modeling Language) source file.

{SIMICS_CONCEPTS}

File: {file_path}
Device: {device_name if device_name else 'Unknown'}
Language: DML

Code:
```dml
{content_preview}
```

Provide a concise 2-3 sentence summary covering:
1. What device or component this file implements
2. Key hardware features (registers, interfaces, protocols)
3. Main functionality (initialization, data transfer, interrupts, etc.)

Focus on hardware behavior and Simics-specific concepts.

Summary:"""
    
    elif language == 'python':
        prompt = f"""You are analyzing a Simics Python source file.

{SIMICS_CONCEPTS}

File: {file_path}
Language: Python (Simics integration)

Code:
```python
{content_preview}
```

Provide a concise 2-3 sentence summary covering:
1. What this Python module does in the Simics context
2. Key classes, functions, or device implementations
3. How it integrates with Simics (device models, scripts, utilities)

Focus on Simics-specific functionality.

Summary:"""
    
    else:
        # Generic fallback
        prompt = f"""Analyze this {language} source code file.

File: {file_path}

Code:
```
{content_preview}
```

Provide a concise 2-3 sentence summary of what this file implements.

Summary:"""
    
    try:
        response = create_chat_completion_iflow(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        summary = response["choices"][0]["message"]["content"].strip()
        
        # Remove any markdown formatting
        summary = summary.replace("**", "").replace("*", "")
        
        return summary
        
    except Exception as e:
        print(f"Warning: Failed to generate file summary: {e}")
        # Fallback to basic description
        if language == 'dml' and device_name:
            return f"DML device model for {device_name}"
        elif language == 'python':
            return f"Python module for Simics: {os.path.basename(file_path)}"
        else:
            return f"{language.upper()} source file: {os.path.basename(file_path)}"


def generate_chunk_summary(
    chunk_code: str,
    file_summary: str,
    metadata: Dict[str, Any],
    model: str = "iflow/qwen3-coder-plus",
    max_tokens: int = 150
) -> str:
    """
    Generate a summary of a specific code chunk with file context.
    
    Args:
        chunk_code: Code chunk content
        file_summary: Summary of the entire file
        metadata: Chunk metadata (language, chunk_type, etc.)
        model: Model to use for summarization
        max_tokens: Maximum tokens for summary
        
    Returns:
        Chunk-level summary string
    """
    language = metadata.get('language', 'unknown')
    chunk_type = metadata.get('chunk_type', 'unknown')
    device_name = metadata.get('device_name', '')
    
    # Truncate chunk if too long
    chunk_preview = chunk_code[:2000]
    if len(chunk_code) > 2000:
        chunk_preview += "\n... (truncated)"
    
    # Build Simics-specific prompt
    if language == 'dml':
        prompt = f"""You are analyzing a code chunk from a Simics DML device model.

File Context: {file_summary}
Device: {device_name if device_name else 'Unknown'}
Chunk Type: {chunk_type}

Code Chunk:
```dml
{chunk_preview}
```

Provide a concise 1-2 sentence summary of what THIS SPECIFIC code chunk does.
Focus on:
- Specific registers, fields, or methods defined
- Hardware behavior implemented
- Interfaces or protocols used
- Data flow or state management

Be specific to this chunk, not the overall file.

Summary:"""
    
    elif language == 'python':
        prompt = f"""You are analyzing a code chunk from a Simics Python module.

File Context: {file_summary}
Chunk Type: {chunk_type}

Code Chunk:
```python
{chunk_preview}
```

Provide a concise 1-2 sentence summary of what THIS SPECIFIC code chunk does.
Focus on:
- Specific classes, functions, or methods
- Simics API usage
- Device interactions or configurations
- Utility functions or helpers

Be specific to this chunk, not the overall file.

Summary:"""
    
    else:
        # Generic fallback
        prompt = f"""Analyze this code chunk.

File Context: {file_summary}

Code Chunk:
```
{chunk_preview}
```

Provide a concise 1-2 sentence summary of what this specific code chunk does.

Summary:"""
    
    try:
        response = create_chat_completion_iflow(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        summary = response["choices"][0]["message"]["content"].strip()
        
        # Remove any markdown formatting
        summary = summary.replace("**", "").replace("*", "")
        
        return summary
        
    except Exception as e:
        print(f"Warning: Failed to generate chunk summary: {e}")
        # Fallback to basic description
        if chunk_type and chunk_type != 'unknown':
            return f"{chunk_type.replace('_', ' ').title()} implementation"
        else:
            return f"Code segment from {language} file"


def test_summarization():
    """Test the summarization functions."""
    # Test DML file summary
    dml_code = """
dml 1.4;

device uart_controller;

constant FIFO_SIZE = 16;

bank regs {
    register ctrl size 4 @ 0x00 {
        field enable @ [0];
        field mode @ [2:1];
    }
    
    register status size 4 @ 0x04 {
        field tx_ready @ [0];
        field rx_ready @ [1];
    }
}

method init() {
    log info: "UART initialized";
}
"""
    
    metadata = {
        'language': 'dml',
        'file_path': 'devices/uart_controller.dml',
        'device_name': 'uart_controller'
    }
    
    print("Testing file-level summarization...")
    file_summary = generate_file_summary(dml_code, metadata)
    print(f"File Summary: {file_summary}\n")
    
    # Test chunk summary
    chunk_code = """
bank regs {
    register ctrl size 4 @ 0x00 {
        field enable @ [0];
        field mode @ [2:1];
    }
    
    register status size 4 @ 0x04 {
        field tx_ready @ [0];
        field rx_ready @ [1];
    }
}
"""
    
    chunk_metadata = metadata.copy()
    chunk_metadata['chunk_type'] = 'register_definitions'
    
    print("Testing chunk-level summarization...")
    chunk_summary = generate_chunk_summary(chunk_code, file_summary, chunk_metadata)
    print(f"Chunk Summary: {chunk_summary}")


if __name__ == "__main__":
    test_summarization()
