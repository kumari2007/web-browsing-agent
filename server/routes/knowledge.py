"""
Knowledge Base and RAG management API endpoints.
Provides document uploading (TXT, MD, PDF), chunk inspection, deletion, and semantic search.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from rag.document_service import KnowledgeBaseService

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])
kb_service = KnowledgeBaseService()


class SearchKnowledgeRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    min_similarity: float = Field(default=0.15, ge=0.0, le=1.0, description="Minimum cosine similarity")


@router.post("/upload", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document (TXT, Markdown, or PDF) into the RAG vector store."""
    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        res = kb_service.ingest_file_bytes(
            filename=file.filename or "uploaded_document.txt",
            file_bytes=content_bytes
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("")
async def list_documents():
    """List all indexed documents, chunk counts, and source provenance."""
    return kb_service.list_documents()


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Remove a document and its embedding chunks from the vector store."""
    success = kb_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or already deleted")
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/search")
async def search_knowledge(req: SearchKnowledgeRequest):
    """Perform semantic vector retrieval across all indexed knowledge chunks."""
    results = kb_service.search_knowledge(
        query=req.query,
        top_k=req.top_k,
        min_similarity=req.min_similarity
    )
    return {
        "query": req.query,
        "count": len(results),
        "results": results
    }
