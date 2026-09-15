"""Business logic and orchestration service layer.

Connects ingestion, vector storage, retrieval, and LLM answer generation
with citation tracking and compliance verification.
"""

from .context_injection import (
    ContextInjectionError,
    TokenBudgetExceededError,
    assemble_context,
    build_prompt,
    calculate_effective_context_budget,
    count_tokens,
    format_chunk,
    format_prompt_overview,
    validate_and_sanitize_citations,
)
from .conversational_rag import (
    ConversationSession,
    conversational_answer,
    format_conversation_history,
    rewrite_followup,
    trim_conversation_history,
    validate_rewritten_query,
)
from .document_upload import (
    ChunkingError,
    DocumentRecord,
    DocumentStatus,
    DocumentStatusTracker,
    DocumentUploadError,
    EmptyDocumentError,
    EmptyFileError,
    ExtractionError,
    FileOversizedError,
    IndexingError,
    InvalidFilenameError,
    UnsupportedFileTypeError,
    get_status_tracker,
    process_uploaded_document,
    sanitize_filename,
    store_upload,
    validate_file_extension,
)
from .guardrails import (
    evaluate_retrieval_strength,
    format_guardrail_report,
    get_chunk_score,
    guarded_answer,
    retrieval_is_strong,
)
from .llm import LLMConfigurationError, LLMServiceError, generate_answer, generate_grounded_answer

__all__ = [
    "generate_answer",
    "generate_grounded_answer",
    "LLMConfigurationError",
    "LLMServiceError",
    "format_chunk",
    "count_tokens",
    "assemble_context",
    "build_prompt",
    "calculate_effective_context_budget",
    "format_prompt_overview",
    "ContextInjectionError",
    "TokenBudgetExceededError",
    "retrieval_is_strong",
    "evaluate_retrieval_strength",
    "guarded_answer",
    "get_chunk_score",
    "format_guardrail_report",
    "rewrite_followup",
    "conversational_answer",
    "format_conversation_history",
    "trim_conversation_history",
    "validate_rewritten_query",
    "ConversationSession",
    "store_upload",
    "process_uploaded_document",
    "validate_file_extension",
    "sanitize_filename",
    "get_status_tracker",
    "DocumentStatusTracker",
    "DocumentRecord",
    "DocumentStatus",
    "DocumentUploadError",
    "UnsupportedFileTypeError",
    "EmptyFileError",
    "FileOversizedError",
    "InvalidFilenameError",
    "ExtractionError",
    "EmptyDocumentError",
    "ChunkingError",
    "IndexingError",
]



