#!/usr/bin/env python3
"""Retrieval-Augmented Generation (RAG) pipeline for HarchOS.

A complete RAG pipeline that:
1. Embeds documents using sentence-transformers
2. Indexes them in FAISS for fast similarity search
3. Retrieves top-k relevant chunks for a user query
4. Generates grounded answers with an LLM

Usage:
    python rag_pipeline.py --port 8080
"""

import argparse
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Optional

import numpy as np

# FAISS for vector similarity search
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("[WARN] faiss-cpu not installed — using brute-force search")

# Sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    print("[WARN] sentence-transformers not installed — using dummy embeddings")

# LLM for generation
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("[WARN] transformers not installed — retrieval-only mode")


# ---------------------------------------------------------------------------
# Document store and embedding
# ---------------------------------------------------------------------------

class DocumentStore:
    """Manages document indexing and retrieval with FAISS."""

    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []  # List of {"title": str, "content": str}
        self.chunks = []     # List of str
        self.embeddings = None
        self.index = None

        # Load embedding model
        if ST_AVAILABLE:
            print(f"Loading embedding model: {embedding_model_name}...")
            self.embedder = SentenceTransformer(embedding_model_name)
            self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        else:
            self.embedder = None
            self.embedding_dim = 384  # Default for all-MiniLM-L6-v2

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = " ".join(words[i:i + self.chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks if chunks else [text]

    def add_documents(self, documents: List[dict]):
        """Add documents to the store and rebuild the index."""
        for doc in documents:
            title = doc.get("title", "Untitled")
            content = doc.get("content", "")
            self.documents.append({"title": title, "content": content})
            chunks = self.chunk_text(content)
            for chunk in chunks:
                self.chunks.append(f"[{title}] {chunk}")

        print(f"Total documents: {len(self.documents)}, Total chunks: {len(self.chunks)}")
        self._build_index()

    def _build_index(self):
        """Build or rebuild the FAISS index."""
        if not self.chunks:
            return

        # Generate embeddings
        if self.embedder:
            print("Encoding chunks...")
            self.embeddings = self.embedder.encode(
                self.chunks, show_progress_bar=True, normalize_embeddings=True
            )
        else:
            # Random embeddings fallback
            self.embeddings = np.random.randn(len(self.chunks), self.embedding_dim)
            self.embeddings = self.embeddings / np.linalg.norm(
                self.embeddings, axis=1, keepdims=True
            )

        # Build FAISS index
        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.index.add(self.embeddings.astype(np.float32))
        else:
            self.index = None  # Will use brute-force

        print(f"Index built with {len(self.chunks)} chunks")

    def retrieve(self, query: str, top_k: int = 3) -> List[dict]:
        """Retrieve the top-k most relevant chunks for a query."""
        if not self.chunks:
            return []

        # Embed query
        if self.embedder:
            query_embedding = self.embedder.encode(
                [query], normalize_embeddings=True
            )
        else:
            query_embedding = np.random.randn(1, self.embedding_dim)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Search
        if FAISS_AVAILABLE and self.index is not None:
            scores, indices = self.index.search(query_embedding.astype(np.float32), top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.chunks):
                    results.append({
                        "chunk": self.chunks[idx],
                        "score": float(score),
                    })
            return results
        else:
            # Brute-force cosine similarity
            similarities = np.dot(self.embeddings, query_embedding.T).flatten()
            top_indices = np.argsort(similarities)[::-1][:top_k]
            return [
                {"chunk": self.chunks[i], "score": float(similarities[i])}
                for i in top_indices
            ]

    @property
    def stats(self) -> dict:
        """Return index statistics."""
        return {
            "num_documents": len(self.documents),
            "num_chunks": len(self.chunks),
            "embedding_dim": self.embedding_dim,
            "index_type": "faiss" if self.index is not None else "brute_force",
        }


# ---------------------------------------------------------------------------
# LLM generator
# ---------------------------------------------------------------------------

class RAGGenerator:
    """Generates answers using retrieved context and an LLM."""

    def __init__(self, model_name: str = "meta-llama/Llama-2-7b-chat-hf",
                 device: str = "auto"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None

        if not TRANSFORMERS_AVAILABLE:
            print("[WARN] No LLM available — using extractive answering")

    def load(self):
        """Lazily load the LLM."""
        if self._model is not None or not TRANSFORMERS_AVAILABLE:
            return

        print(f"Loading LLM: {self.model_name}...")
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=True)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name, torch_dtype=dtype, device_map=self.device
        )
        self._model.eval()
        print("LLM loaded")

    def generate(self, question: str, context_chunks: List[str],
                 max_tokens: int = 256, temperature: float = 0.3) -> dict:
        """Generate an answer using retrieved context."""
        context = "\n\n".join(f"[Source {i+1}]: {chunk}"
                              for i, chunk in enumerate(context_chunks))

        # If LLM is available, generate with it
        if self._model is not None:
            prompt = (
                f"Answer the question based on the following context. "
                f"If the context doesn't contain the answer, say so.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question}\n\nAnswer:"
            )
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
            input_length = inputs["input_ids"].shape[1]

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=max(temperature, 1e-8),
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            new_tokens = outputs[0][input_length:]
            answer = self._tokenizer.decode(new_tokens, skip_special_tokens=True)

            return {
                "answer": answer,
                "sources": context_chunks,
                "num_sources": len(context_chunks),
            }

        # Fallback: extractive answering
        return {
            "answer": f"Based on the retrieved context:\n{context}",
            "sources": context_chunks,
            "num_sources": len(context_chunks),
            "note": "LLM not available — returning raw context",
        }


# ---------------------------------------------------------------------------
# Sample documents for demo
# ---------------------------------------------------------------------------

SAMPLE_DOCUMENTS = [
    {
        "title": "HarchOS Overview",
        "content": (
            "HarchOS is a sustainable AI compute platform developed by HarchCorp. "
            "It provides a serverless GPU compute layer that automatically schedules "
            "workloads across distributed hubs based on carbon intensity, cost, and "
            "latency. HarchOS supports PyTorch, TensorFlow, and JAX workloads with "
            "seamless scaling from a single GPU to multi-node clusters. The platform "
            "integrates carbon-aware scheduling to minimize the environmental impact "
            "of AI training and inference."
        ),
    },
    {
        "title": "HarchOS SDK",
        "content": (
            "The HarchOS Python SDK (pip install harchos) provides a programmatic "
            "interface to the HarchOS platform. Key features include: workload "
            "submission and management, real-time carbon intensity queries, multi-hub "
            "deployment orchestration, metrics collection and monitoring, and "
            "cost optimization APIs. The SDK requires Python 3.9+ and can be used "
            "both locally and within HarchOS workloads."
        ),
    },
    {
        "title": "Carbon-Aware Scheduling",
        "content": (
            "HarchOS's carbon-aware scheduling engine monitors real-time grid carbon "
            "intensity data from multiple electricity grid operators. When carbon "
            "intensity exceeds a configurable threshold, the scheduler can: pause "
            "training jobs and resume later, migrate workloads to lower-carbon "
            "regions, defer non-urgent batch jobs, and route inference traffic to "
            "greener hubs. This approach can reduce the carbon footprint of AI "
            "workloads by 30-60% with minimal impact on throughput."
        ),
    },
    {
        "title": "Multi-Hub Architecture",
        "content": (
            "HarchOS operates a network of compute hubs distributed across multiple "
            "geographic regions and cloud providers. Each hub has its own GPU fleet, "
            "storage, and networking. The Hub Orchestration Layer (HOL) manages: "
            "cross-hub workload placement, data replication and synchronization, "
            "latency-based routing for inference, and failover handling. Users can "
            "deploy workloads to specific hubs or let HarchOS choose the optimal "
            "location automatically."
        ),
    },
]


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

doc_store: Optional[DocumentStore] = None
generator: Optional[RAGGenerator] = None


class RAGHandler(BaseHTTPRequestHandler):
    """HTTP handler for the RAG pipeline."""

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "index": doc_store.stats,
            }).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid JSON"}).encode())
            return

        if self.path == "/query":
            question = data.get("question", "")
            top_k = data.get("top_k", 3)
            max_tokens = data.get("max_tokens", 256)
            temperature = data.get("temperature", 0.3)

            if not question:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "question is required"}).encode())
                return

            start = time.time()
            retrieved = doc_store.retrieve(question, top_k=top_k)
            context_chunks = [r["chunk"] for r in retrieved]
            result = generator.generate(
                question, context_chunks, max_tokens=max_tokens,
                temperature=temperature
            )
            elapsed = time.time() - start

            result["retrieval_time_seconds"] = round(elapsed, 3)
            result["retrieval_scores"] = [r["score"] for r in retrieved]
            self._set_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())

        elif self.path == "/index":
            documents = data.get("documents", [])
            if not documents:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "documents list is required"}).encode())
                return

            doc_store.add_documents(documents)
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "indexed",
                "stats": doc_store.stats,
            }).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline Server")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--embedding-model", type=str, default="all-MiniLM-L6-v2")
    parser.add_argument("--llm-model", type=str, default="meta-llama/Llama-2-7b-chat-hf")
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--no-sample-data", action="store_true",
                        help="Skip loading sample documents")
    parser.add_argument("--build-index-only", action="store_true",
                        help="Build FAISS index and exit without starting the server")
    args = parser.parse_args()

    global doc_store, generator

    # Initialize document store
    doc_store = DocumentStore(
        embedding_model_name=args.embedding_model,
        chunk_size=512,
        chunk_overlap=64,
    )

    # Initialize generator
    generator = RAGGenerator(model_name=args.llm_model, device=args.device)
    generator.load()

    # Load sample data
    if not args.no_sample_data:
        print("\nLoading sample documents...")
        doc_store.add_documents(SAMPLE_DOCUMENTS)

    # If --build-index-only, exit after building the index
    if args.build_index_only:
        print("\nIndex built successfully!")
        print(f"  Documents: {doc_store.stats['num_documents']}")
        print(f"  Chunks: {doc_store.stats['num_chunks']}")
        print(f"  Index type: {doc_store.stats['index_type']}")
        return

    # Start server
    server = HTTPServer((args.host, args.port), RAGHandler)
    print(f"\nRAG Pipeline Server running on http://{args.host}:{args.port}")
    print("  POST /query   — ask a question")
    print("  POST /index   — add documents")
    print("  GET  /health  — health check")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
