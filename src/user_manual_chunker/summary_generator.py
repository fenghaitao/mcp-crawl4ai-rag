"""
Summary generator for user manual documentation chunks.

Generates concise summaries using LLM-based generation with fallback to
extractive summaries for error cases.
"""

import re
import logging
import signal
from typing import Optional
from contextlib import contextmanager
from .data_models import ChunkMetadata
from .interfaces import DocumentChunk

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Exception raised when operation times out."""
    pass


@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for timeout handling.
    
    Args:
        seconds: Timeout in seconds
        
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set up signal handler (Unix-like systems only)
    try:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    except (AttributeError, ValueError):
        # signal.SIGALRM not available (Windows) - just yield without timeout
        logger.warning("Timeout not supported on this platform")
        yield


class SummaryGenerator:
    """Generate concise summaries for documentation chunks."""
    
    def __init__(
        self,
        model: str = "iflow/qwen3-coder-plus",
        max_summary_length: int = 150,
        timeout: int = 30
    ):
        """
        Initialize summary generator.
        
        Args:
            model: Model to use for LLM-based summaries
            max_summary_length: Maximum length of generated summaries in words
            timeout: Timeout for LLM requests in seconds
        """
        self.model = model
        self.max_summary_length = max_summary_length
        self.timeout = timeout
        
    def generate_summary(
        self,
        chunk: DocumentChunk,
        doc_context: str,
        metadata: ChunkMetadata
    ) -> str:
        """
        Generate summary using LLM with fallback to extractive summary.
        
        Handles LLM failures, timeouts, and empty content gracefully.
        
        Args:
            chunk: Document chunk to summarize
            doc_context: Context about the overall document
            metadata: Chunk metadata for context
            
        Returns:
            Generated summary string
        """
        # Handle empty content
        if not chunk or not chunk.content or not chunk.content.strip():
            logger.warning("Empty chunk content, generating summary from metadata")
            return self._generate_summary_from_metadata(metadata)
        
        try:
            # Try LLM-based summary first with timeout
            summary = self._generate_llm_summary(chunk, doc_context, metadata)
            
            # Validate summary
            if not summary or not summary.strip():
                logger.warning("LLM returned empty summary, using fallback")
                return self._fallback_summary(chunk, metadata)
            
            # Enforce length constraint
            summary = self._enforce_length_limit(summary)
            
            return summary
            
        except TimeoutError as e:
            logger.warning(f"LLM summary generation timed out: {e}")
            return self._fallback_summary(chunk, metadata)
            
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}")
            # Fall back to extractive summary
            return self._fallback_summary(chunk, metadata)
    
    def _generate_llm_summary(
        self,
        chunk: DocumentChunk,
        doc_context: str,
        metadata: ChunkMetadata
    ) -> str:
        """
        Generate summary using LLM with timeout handling.
        
        Uses the code_summarizer.generate_documentation_summary function
        which provides documentation-specific prompts.
        
        Args:
            chunk: Document chunk
            doc_context: Document context
            metadata: Chunk metadata
            
        Returns:
            LLM-generated summary
            
        Raises:
            TimeoutError: If LLM call exceeds timeout
            Exception: If LLM call fails
        """
        # Try to use code_summarizer's documentation summary function
        try:
            from src.code_summarizer import generate_documentation_summary
            
            # Call with timeout
            with timeout_context(self.timeout):
                summary = generate_documentation_summary(
                    chunk=chunk,
                    doc_context=doc_context,
                    metadata=metadata,
                    model=self.model,
                    max_tokens=self.max_summary_length * 2
                )
                
                return summary
                
        except ImportError:
            logger.warning("Could not import code_summarizer, using fallback implementation")
            # Fall back to local implementation
            return self._generate_llm_summary_fallback(chunk, doc_context, metadata)
        except TimeoutError:
            logger.warning(f"LLM call timed out after {self.timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _generate_llm_summary_fallback(
        self,
        chunk: DocumentChunk,
        doc_context: str,
        metadata: ChunkMetadata
    ) -> str:
        """
        Fallback LLM summary generation (direct implementation).
        
        Used when code_summarizer is not available.
        
        Args:
            chunk: Document chunk
            doc_context: Document context
            metadata: Chunk metadata
            
        Returns:
            LLM-generated summary
            
        Raises:
            TimeoutError: If LLM call exceeds timeout
            Exception: If LLM call fails
        """
        # Import here to avoid circular dependency
        from src.iflow_client import create_chat_completion_iflow
        
        # Build documentation-specific prompt
        prompt = self._build_documentation_prompt(chunk, doc_context, metadata)
        
        # Call LLM with timeout
        try:
            with timeout_context(self.timeout):
                response = create_chat_completion_iflow(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.3,
                    max_tokens=self.max_summary_length * 2  # Allow some buffer
                )
                
                # Validate response structure
                if not response or "choices" not in response:
                    raise ValueError("Invalid response structure from LLM")
                
                if not response["choices"] or len(response["choices"]) == 0:
                    raise ValueError("No choices in LLM response")
                
                if "message" not in response["choices"][0]:
                    raise ValueError("No message in LLM response choice")
                
                summary = response["choices"][0]["message"]["content"].strip()
                
                # Clean up markdown formatting
                summary = summary.replace("**", "").replace("*", "")
                
                # Remove "Summary:" prefix if present
                summary = re.sub(r'^Summary:\s*', '', summary, flags=re.IGNORECASE)
                
                return summary
                
        except TimeoutError:
            logger.warning(f"LLM call timed out after {self.timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _build_documentation_prompt(
        self,
        chunk: DocumentChunk,
        doc_context: str,
        metadata: ChunkMetadata
    ) -> str:
        """
        Build documentation-specific prompt for LLM.
        
        Args:
            chunk: Document chunk
            doc_context: Document context
            metadata: Chunk metadata
            
        Returns:
            Formatted prompt string
        """
        # Get heading hierarchy for context
        heading_path = " > ".join(metadata.heading_hierarchy) if metadata.heading_hierarchy else "Unknown Section"
        
        # Truncate chunk content if too long
        content = chunk.content
        if len(content) > 2000:
            content = content[:2000] + "\n... (truncated)"
        
        # Check if chunk contains code
        has_code = metadata.contains_code
        code_languages = ", ".join(metadata.code_languages) if metadata.code_languages else "unknown"
        
        # Build prompt based on content type
        if has_code:
            prompt = f"""You are analyzing a section from a technical user manual or documentation.

Document Context: {doc_context}
Section: {heading_path}
Contains Code: Yes ({code_languages})

Content:
{content}

Provide a concise 1-2 sentence summary of this documentation section.
Focus on:
- What concept, feature, or API is being explained
- The purpose of any code examples shown
- Key technical details or parameters
- How this relates to the broader documentation topic

Be specific and mention the code examples if present.

Summary:"""
        else:
            prompt = f"""You are analyzing a section from a technical user manual or documentation.

Document Context: {doc_context}
Section: {heading_path}

Content:
{content}

Provide a concise 1-2 sentence summary of this documentation section.
Focus on:
- What concept, feature, or topic is being explained
- Key information or instructions provided
- How this relates to the broader documentation topic

Be specific and informative.

Summary:"""
        
        return prompt
    
    def _fallback_summary(
        self,
        chunk: DocumentChunk,
        metadata: ChunkMetadata
    ) -> str:
        """
        Generate extractive summary as fallback.
        
        Handles empty content gracefully.
        
        Args:
            chunk: Document chunk
            metadata: Chunk metadata
            
        Returns:
            Extractive summary string
        """
        # Handle empty chunk
        if not chunk or not chunk.content:
            return self._generate_summary_from_metadata(metadata)
        
        content = chunk.content.strip()
        
        # Handle empty content
        if not content:
            return self._generate_summary_from_metadata(metadata)
        
        # Try to extract first meaningful sentence
        try:
            sentences = re.split(r'[.!?]\s+', content)
            
            # Filter out very short sentences and headings
            meaningful_sentences = [
                s.strip() for s in sentences 
                if len(s.strip()) > 20 and not s.strip().startswith('#')
            ]
            
            if meaningful_sentences:
                # Use first sentence
                summary = meaningful_sentences[0]
                
                # Add code mention if present
                if metadata.contains_code:
                    code_langs = ", ".join(metadata.code_languages) if metadata.code_languages else "code"
                    summary += f" Includes {code_langs} examples."
                
                # Enforce length limit
                summary = self._enforce_length_limit(summary)
                return summary
        except Exception as e:
            logger.warning(f"Error extracting sentences: {e}")
        
        # If extraction failed, use metadata-based summary
        return self._generate_summary_from_metadata(metadata)
    
    def _generate_summary_from_metadata(self, metadata: ChunkMetadata) -> str:
        """
        Generate summary from metadata when content is unavailable.
        
        Args:
            metadata: Chunk metadata
            
        Returns:
            Metadata-based summary string
        """
        # Use heading hierarchy if available
        if metadata.heading_hierarchy:
            heading = metadata.heading_hierarchy[-1]
            if metadata.contains_code:
                return f"Documentation for {heading} with code examples."
            else:
                return f"Documentation for {heading}."
        
        # Last resort - generic summary
        if metadata.contains_code:
            code_langs = ", ".join(metadata.code_languages) if metadata.code_languages else "code"
            return f"Technical documentation section with {code_langs} examples."
        else:
            return "Technical documentation section."
    
    def _enforce_length_limit(self, summary: str) -> str:
        """
        Enforce maximum summary length.
        
        Args:
            summary: Summary text
            
        Returns:
            Truncated summary if needed
        """
        words = summary.split()
        
        if len(words) <= self.max_summary_length:
            return summary
        
        # Truncate to max length
        truncated = ' '.join(words[:self.max_summary_length])
        
        # Try to end at a sentence boundary
        last_period = truncated.rfind('.')
        if last_period > len(truncated) * 0.7:  # If period is in last 30%
            return truncated[:last_period + 1]
        
        # Otherwise just add ellipsis
        return truncated + "..."


def test_summary_generator():
    """Test the summary generator with sample documentation."""
    from .data_models import Section, Heading, Paragraph, CodeBlock
    
    # Create sample chunk with code
    heading = Heading(level=2, text="Device Initialization", line_number=10)
    
    paragraphs = [
        Paragraph(
            content="The device must be initialized before use. Call the init() method to configure registers.",
            line_start=11,
            line_end=11
        )
    ]
    
    code_blocks = [
        CodeBlock(
            content="device.init()\ndevice.configure(mode='async')",
            language="python",
            line_start=13,
            line_end=14
        )
    ]
    
    section = Section(
        heading=heading,
        paragraphs=paragraphs,
        code_blocks=code_blocks
    )
    
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=0,
        line_start=10,
        line_end=14
    )
    
    metadata = ChunkMetadata(
        source_file="manual.md",
        heading_hierarchy=["User Guide", "Device Initialization"],
        section_level=2,
        contains_code=True,
        code_languages=["python"],
        chunk_index=0,
        line_start=10,
        line_end=14,
        char_count=len(chunk.content)
    )
    
    # Test summary generation
    generator = SummaryGenerator(max_summary_length=50)
    
    print("Testing summary generation...")
    print(f"Chunk content:\n{chunk.content}\n")
    
    # Test fallback summary (without LLM)
    print("Testing fallback summary...")
    fallback = generator._fallback_summary(chunk, metadata)
    print(f"Fallback summary: {fallback}\n")
    
    # Test LLM summary (if API key available)
    try:
        doc_context = "Simics Device Modeling Language Reference Manual"
        summary = generator.generate_summary(chunk, doc_context, metadata)
        print(f"LLM summary: {summary}")
    except Exception as e:
        print(f"LLM summary test skipped: {e}")


if __name__ == "__main__":
    test_summary_generator()
