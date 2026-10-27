"""RAG package providing document chunking, embeddings, vector indexing, retrieval, and generation."""

from .chunker import TextChunker, TextChunk
from .embeddings import EmbeddingEngine
from .vector_store import VectorStore
from .document_processor import DocumentProcessor
from .retriever import HybridRetriever, RetrievedEvidence
from .answer_generator import AnswerGenerator
from .document_service import KnowledgeBaseService
from .llm_provider import BaseLLMProvider, get_llm_provider

__all__ = [
    "TextChunker",
    "TextChunk",
    "EmbeddingEngine",
    "VectorStore",
    "DocumentProcessor",
    "HybridRetriever",
    "RetrievedEvidence",
    "AnswerGenerator",
    "KnowledgeBaseService",
    "BaseLLMProvider",
    "get_llm_provider",
]
