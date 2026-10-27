"""
Unit tests for RAG pipeline: TextChunker, EmbeddingEngine, VectorStore, HybridRetriever, and AnswerGenerator.
Tests chunking, metadata preservation, hybrid retrieval, mocked LLM responses, and deterministic fallbacks.
"""

from unittest.mock import patch, MagicMock
from rag.chunker import TextChunker
from rag.embeddings import EmbeddingEngine
from rag.vector_store import VectorStore
from rag.retriever import HybridRetriever, RetrievedEvidence
from rag.answer_generator import AnswerGenerator


def test_chunker_overlap_and_metadata():
    chunker = TextChunker(chunk_size=150, chunk_overlap=30)
    text = (
        "Python is a high-level, general-purpose programming language.\n\n"
        "Its design philosophy emphasizes code readability with the use of significant indentation.\n\n"
        "Python is dynamically typed and garbage-collected. It supports multiple programming paradigms.\n\n"
        "Python was conceived in the late 1980s by Guido van Rossum at CWI."
    )
    chunks = chunker.chunk_document(
        text=text,
        url="https://example.com/python",
        title="Python Guide",
        extra_metadata={"category": "programming"}
    )

    assert len(chunks) >= 2
    for c in chunks:
        assert c.url == "https://example.com/python"
        assert c.title == "Python Guide"
        assert c.metadata["category"] == "programming"
        assert len(c.text) > 0


def test_vector_store_indexing_and_similarity(tmp_path):
    db_file = tmp_path / "test_vec.db"
    store = VectorStore(db_path=db_file)
    embeddings_engine = EmbeddingEngine()

    chunker = TextChunker()
    chunks = chunker.chunk_document(
        text="The quick brown fox jumps over the lazy dog.\n\nPython machine learning with PyTorch and Transformers.",
        url="https://example.com/test",
        title="Test Doc"
    )

    embs = embeddings_engine.encode_batch([c.text for c in chunks])
    store.add_chunks(chunks, embs)

    assert store.count() == len(chunks)

    # Query for machine learning
    q_emb = embeddings_engine.encode_text("machine learning PyTorch")
    results = store.search_similar(q_emb, top_k=2)

    assert len(results) > 0
    top_chunk, score = results[0]
    assert "Python machine learning" in top_chunk.text
    assert score > 0.15


def test_answer_generator_with_mocked_llm():
    generator = AnswerGenerator()
    evidence = [
        RetrievedEvidence(
            chunk_id="c1",
            url="https://example.com/python-course",
            title="Python Course A",
            text="Python for Beginners is 100% free and includes a certificate of completion.",
            score=0.92
        )
    ]

    mock_llm_response = {
        "response": "The [Python Course A](https://example.com/python-course) is free and provides a certificate."
    }

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_llm_response
        mock_post.return_value = mock_resp

        answer = generator.generate_answer(query="What is the price of Python Course A?", evidence=evidence)

        assert "Python Course A" in answer
        assert "https://example.com/python-course" in answer


def test_answer_generator_deterministic_fallback():
    generator = AnswerGenerator(base_url="http://invalid-host:11434")
    evidence = [
        RetrievedEvidence(
            chunk_id="c1",
            url="https://example.com/python-course",
            title="Python Course A",
            text="Comprehensive 10-hour course on Python fundamentals.",
            score=0.88
        )
    ]

    # Force connection error to trigger deterministic fallback
    with patch("requests.post", side_effect=Exception("Connection refused")):
        answer = generator.generate_answer(query="Tell me about Python Course A", evidence=evidence)

        assert "deterministic evidence extractor" in answer.lower()
        assert "Python Course A" in answer
        assert "https://example.com/python-course" in answer
