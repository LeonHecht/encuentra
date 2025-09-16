# Copyright 2025 Leon Hecht
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

import json
from pathlib import Path
from rank_bm25 import BM25Okapi
from ..core.config import settings
import unicodedata
import re


class BM25Search:

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 80

    def __init__(self) -> None:

        self.corpus = {}
        self.tokenized = {}
        self.bm25_models = {}
        self.doc_metadata = {}

    # helper to strip accents
    def strip_accents(self, s: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        )

    # helper to normalize tokens: strip accents, lowercase, and drop non‐letters
    def normalize_token(self, tok: str) -> str:
        tok = self.strip_accents(tok.lower())
        # drop any non-alphanumeric characters to match test queries
        tok = re.sub(r"[^a-z0-9]+", "", tok)
        return tok

    def _chunk_document(self, text: str) -> list[dict]:
        """Split a document into overlapping chunks."""

        words = text.split()
        if not words:
            return []

        chunk_size = max(self.CHUNK_SIZE, 1)
        overlap = max(0, min(self.CHUNK_OVERLAP, chunk_size - 1))
        step = max(chunk_size - overlap, 1)

        normalized_words = [self.normalize_token(w) for w in words]

        chunks: list[dict] = []
        start = 0
        chunk_idx = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk_tokens = [tok for tok in normalized_words[start:end] if tok]
            chunk_text = " ".join(chunk_words).strip()
            if chunk_text and chunk_tokens:
                chunks.append(
                    {
                        "chunk_idx": chunk_idx,
                        "chunk_text": chunk_text,
                        "tokens": chunk_tokens,
                    }
                )
                chunk_idx += 1
            start += step

        return chunks

    def _build_download_url(self, doc_id: str) -> str | None:
        for ext in (".pdf", ".PDF", ".htm", ".html", ".HTML", ".docx", ".doc", ".txt"):
            candidate = Path(settings.CORPUS_PATH) / "files" / f"{doc_id}{ext}"
            if candidate.exists():
                return f"/files/{candidate.name}"
        return None

    def index(self, space="supreme_court"):
        """Load documents from CORPUS_PATH into BM25 index."""
        
        print("Loading corpus and initializing BM25 index...")

        self.corpus[space] = []  # dict to hold documents for the space
        self.tokenized[space] = []  # list to hold tokenized documents for the space
        self.doc_metadata[space] = {}

        if space == "supreme_court":
            jsonl_file = Path(settings.CORPUS_PATH) / "corpus.jsonl"
            if jsonl_file.exists():
                # Load JSONL format
                with jsonl_file.open(encoding="utf-8") as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        
                        doc_id_raw = obj.get("id")
                        doc_id = str(doc_id_raw) if doc_id_raw is not None else f"{space}_{len(self.doc_metadata[space])}"

                        title = obj.get("title", "")

                        text = obj.get("text", "")

                        content = f"{title} {text}".strip()
                        self.doc_metadata[space][doc_id] = {"title": title}

                        for chunk in self._chunk_document(content):
                            chunk_id = f"{doc_id}#c{chunk['chunk_idx']}"
                            self.corpus[space].append(
                                {
                                    "id": chunk_id,
                                    "doc_id": doc_id,
                                    "title": title,
                                    "chunk_idx": chunk["chunk_idx"],
                                    "chunk_text": chunk["chunk_text"],
                                }
                            )
                            self.tokenized[space].append(chunk["tokens"])
            else:
                raise Exception("corpus.jsonl file missing.")
        else:
            # Load .txt files in directory
            dir_path = Path(settings.DATA_UPLOAD) / space
            for file in dir_path.glob("**/*.txt"):
                text = file.read_text(encoding="utf-8")
                doc_id = file.stem
                title = file.stem
                self.doc_metadata[space][doc_id] = {"title": title}
                for chunk in self._chunk_document(text):
                    chunk_id = f"{doc_id}#c{chunk['chunk_idx']}"
                    self.corpus[space].append(
                        {
                            "id": chunk_id,
                            "doc_id": doc_id,
                            "title": title,
                            "chunk_idx": chunk["chunk_idx"],
                            "chunk_text": chunk["chunk_text"],
                        }
                    )
                    self.tokenized[space].append(chunk["tokens"])
        # Build BM25
        tokens = self.tokenized[space]
        if tokens:
            # index only the list for this space
            self.bm25_models[space] = BM25Okapi(tokens)
        else:
            self.bm25_models[space] = None
        print("Done loading corpus and initializing BM25 index.")


    def search(self, query: str, top_k: int = 30, space: str = "supreme_court") -> list[dict]:
        """
        Perform BM25 search over the loaded corpus.

        Parameters
        ----------
        query : str
            The search query string.
        top_k : int
            Number of top results to return.

        Returns top_k results as list of dicts with:
        - id: chunk ID ("{doc_id}#c{i}")
        - score: BM25 score
        - snippet: chunk text
        - download_url: path under /files to fetch the original doc
        """
        print(f"Searching in space '{space}' with query: '{query}' and top_k={top_k}")
        model = self.bm25_models[space]
        if model is None:
            print(f"No BM25 model found for space '{space}'. Please index the corpus first.")
            return []
        
        tokenized_query = [self.normalize_token(t) for t in query.split() if t]
        if not tokenized_query:
            print("Empty query after normalization, returning empty results.")
            return []
        print(f"Searching for query: {tokenized_query}")
        scores = model.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        top_indices = [i for i in top_indices if scores[i] > 0][:top_k]
        
        print(f"Found {len(top_indices)} relevant documents in space '{space}'.")

        results = []
        tokenized_query_cleaned = [tok for tok in tokenized_query if len(tok) > 3]
        if len(tokenized_query_cleaned) > 0:
            tokenized_query = tokenized_query_cleaned
            
        for i in top_indices:
            doc = self.corpus[space][i]
            print(f"Processing chunk ID {doc['id']} with score {scores[i]:.4f}")
            text = doc["chunk_text"]
            print(f"Chunk text length: {len(text)} characters")

            snippet = text

            doc_id = doc["doc_id"]
            file_url = self._build_download_url(doc_id)
            if file_url is None:
                print(f"Warning: No file found for document ID {doc_id}")

            title = doc.get("title") or self.doc_metadata.get(space, {}).get(doc_id, {}).get("title", "")
            results.append({
                "id": doc["id"],
                "title": title,
                "score": float(scores[i]),
                "snippet": snippet,
                "download_url": file_url,
            })
        return results
    

bm25_engine = BM25Search()
