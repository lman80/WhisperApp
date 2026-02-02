"""Text cleanup module using local Llama 3B to remove filler words."""

import re
from typing import Optional

# Lazy loading for faster startup
_model = None
_tokenizer = None


def _load_model():
    """Lazy load the LLM model on first use."""
    global _model, _tokenizer
    
    if _model is None:
        try:
            from mlx_lm import load
            _model, _tokenizer = load("mlx-community/Llama-3.2-3B-Instruct-4bit")
        except ImportError:
            raise ImportError(
                "mlx-lm is not installed. Please install with: pip install mlx-lm"
            )
        except Exception as e:
            # If model loading fails, we'll use regex fallback
            print(f"Warning: Could not load LLM model: {e}")
            print("Using regex-based cleanup as fallback.")
            _model = "FALLBACK"
    
    return _model, _tokenizer


# Prompt template for text formatting - focuses on grammar and dialogue
CLEANUP_PROMPT = """Format this transcription. Output ONLY the formatted text.

Rules:
- Fix grammar and punctuation
- Add quotation marks around dialogue (spoken words)
- Remove filler words (um, uh, like, you know)
- Keep all meaning and content intact
- Output the formatted text only, no explanations

Example:
Input: he said what are you doing here I said I dont know
Output: He said, "What are you doing here?" I said, "I don't know."

Input: {text}
Output:"""


def clean_with_llm(text: str) -> str:
    """Clean transcription using local Llama 3B model."""
    model, tokenizer = _load_model()
    
    if model == "FALLBACK":
        return clean_with_regex(text)
    
    from mlx_lm import generate
    
    prompt = CLEANUP_PROMPT.format(text=text)
    
    # Build the chat format for instruction model
    messages = [{"role": "user", "content": prompt}]
    formatted_prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    response = generate(
        model, 
        tokenizer, 
        prompt=formatted_prompt, 
        max_tokens=min(len(text.split()) * 2, 200),  # Allow more tokens for formatting
        verbose=False
    )
    
    # Extract just the cleaned text (remove any preamble/commentary)
    cleaned = response.strip()
    
    # Remove common LLM commentary patterns (but keep quotation marks for dialogue!)
    import re
    commentary_patterns = [
        r'^(Here[\'"]?s?|The cleaned|Cleaned text|Output|Result|Formatted)[:\s]*',
        r'^\s*-\s*',  # Leading dash
    ]
    for pattern in commentary_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
    
    # If response looks like commentary, fall back to regex
    if any(phrase in cleaned.lower() for phrase in ['it seems', 'i can', 'the text', 'however', 'here is']):
        return clean_with_regex(text)
    
    # If the response is empty or too short, return original
    if not cleaned or len(cleaned) < len(text) * 0.3:
        return text
    
    return cleaned


def clean_with_regex(text: str) -> str:
    """
    Fallback: Remove common filler words using regex.
    Less sophisticated but works without LLM.
    """
    if not text:
        return text
    
    # Common filler words and phrases (case-insensitive)
    filler_patterns = [
        r'\b(um+|uh+|er+|ah+)\b',
        r'\b(like,?\s+)+',  # "like, like,"
        r'\b(you know,?\s*)+',
        r'\b(basically,?\s*)+',
        r'\b(actually,?\s*)+',
        r'\b(literally,?\s*)+',
        r'\b(so,?\s+yeah)\b',
        r'\b(I mean,?\s*)+',
        r'\b(kind of|kinda)\s+',
        r'\b(sort of|sorta)\s+',
    ]
    
    cleaned = text
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    # Remove repeated words (stutters) at start of sentences
    cleaned = re.sub(r'\b(\w+)\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove leading punctuation from cleanup artifacts
    cleaned = re.sub(r'^[\s,;:]+', '', cleaned).strip()
    
    # Fix capitalization after cleanup
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    
    return cleaned


def clean(text: str, use_llm: bool = True) -> str:
    """
    Clean transcription text by removing filler words.
    
    Args:
        text: Raw transcription text
        use_llm: If True, use Llama 3B for intelligent cleanup.
                 If False, use regex-based cleanup (faster).
    
    Returns:
        Cleaned text with filler words removed
    """
    if not text or len(text.strip()) == 0:
        return text
    
    # For very short text, just use regex (LLM overkill)
    if len(text.split()) < 5:
        return clean_with_regex(text)
    
    if use_llm:
        try:
            return clean_with_llm(text)
        except Exception as e:
            print(f"LLM cleanup failed: {e}, using regex fallback")
            return clean_with_regex(text)
    else:
        return clean_with_regex(text)


class TextCleaner:
    """Reusable text cleaner with cached model."""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self._initialized = False
    
    def initialize(self):
        """Pre-load the model for faster first cleanup."""
        if self.use_llm and not self._initialized:
            try:
                _load_model()
                self._initialized = True
            except Exception:
                self.use_llm = False
    
    def clean(self, text: str) -> str:
        """Clean the provided text."""
        return clean(text, use_llm=self.use_llm)
