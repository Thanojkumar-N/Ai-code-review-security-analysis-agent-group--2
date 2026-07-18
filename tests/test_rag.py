import os
import pytest
from backend.app.rag.rag_service import RAGService

def test_rag_ingestion_and_retrieval():
    """Verify that guidelines documents are read, chunked, and retrievable from the ChromaDB client."""
    # Trigger Ingestion
    docs_added = RAGService.ingest_documents("knowledge_base")
    assert docs_added > 0

    # Query SQL Injection guidelines
    sqli_context = RAGService.retrieve_context("SQL Injection")
    assert sqli_context is not None
    assert "parameterize" in sqli_context.lower() or "concatenate" in sqli_context.lower()

    # Query SOLID guidelines
    solid_context = RAGService.retrieve_context("SOLID Principles")
    assert solid_context is not None
    assert "responsibility" in solid_context.lower() or "srp" in solid_context.lower()
