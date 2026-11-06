"""
sha_rag_engine.py - SHA-Specific Retrieval-Augmented Generation (RAG) System
SHA Interface Interiors - AI-Powered Interior Design Lead Management System

Features:
1. Vector Ingestion: Indexes all 46 interior design categories into SQLite table KNOWLEDGE_VECTORS.
2. Embedding Generation: Uses Gemini models/text-embedding-004 with resilient deterministic dense vector fallback.
3. Pure Python Cosine Similarity: Fast, portable, zero binary/C++ build dependencies on Windows.
4. Source Attribution Citations: Grounded responses cite verified standards (e.g. [Source: BIS IS 710:2010]).
5. Confidence Handling: Gracefully defers out-of-scope inquiries to the Miyapur office team.
6. MANDATORY POLICY: All generated RAG answers are generated strictly in ENGLISH ONLY.
"""

import os
import sys
import math
import json
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import datetime

import database
import ai_service
import india_interior_knowledge
import business_config

# Vocabulary tokens for dense semantic fallback vectors
SEMANTIC_VOCABULARY = [
    "plywood", "bwp", "is710", "is303", "mr", "hdhmr", "mdf", "particle", "calibrated",
    "laminate", "acrylic", "veneer", "pu", "paint", "duco", "polyester", "gloss", "matt",
    "countertop", "granite", "quartz", "sintered", "dekton", "corian", "nano", "white",
    "hettich", "blum", "hafele", "sensys", "softclose", "hinge", "runner", "tandembox", "aventos",
    "pantry", "tall", "corner", "lemans", "gola", "handle", "profile", "ergonomics", "triangle",
    "kitchen", "parallel", "island", "chimney", "suction", "duct", "wardrobe", "sliding", "hinged",
    "loft", "glass", "tinted", "lacquered", "walkin", "closet", "ceiling", "gypsum", "gyproc",
    "pop", "cove", "lighting", "3000k", "4000k", "cri", "cob", "spotlight", "magnetic", "track",
    "tv", "unit", "fluted", "louvers", "partition", "mandir", "pooja", "vastu", "ishanya", "balcony",
    "wpc", "decking", "marble", "italian", "gvt", "tiles", "wallpaper", "stucco", "vanity",
    "termite", "borer", "warranty", "timeline", "miyapur", "appointment", "calendar", "quotation"
]
VOCAB_SIZE = len(SEMANTIC_VOCABULARY) + 64


def _deterministic_semantic_vector(text: str, dim: int = 128) -> List[float]:
    """
    Produces a normalized 128-dimensional dense semantic embedding vector
    using vocabulary projection and character n-gram hashing.
    Used for instant, resilient offline retrieval.
    """
    vec = [0.0] * dim
    clean_text = text.lower()
    words = re.findall(r'\b[a-z0-9]{2,}\b', clean_text)

    # 1. Vocabulary weighting
    for word in words:
        for idx, vocab_term in enumerate(SEMANTIC_VOCABULARY):
            if vocab_term in word or word in vocab_term:
                pos = idx % dim
                vec[pos] += 2.0

    # 2. Hashed n-grams
    for word in words:
        h = int(hashlib.md5(word.encode('utf-8')).hexdigest()[:8], 16)
        pos = h % dim
        vec[pos] += 1.0

    # 3. L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 5) for x in vec]
    else:
        vec = [1.0 / math.sqrt(dim)] * dim

    return vec


def generate_embedding(text: str) -> List[float]:
    """
    Generates an embedding vector for the given text.
    Attempts Gemini text-embedding-004 first, falling back to deterministic dense vector.
    """
    clean = text.strip()
    if not clean:
        return [0.0] * 128

    if ai_service.is_gemini_available():
        try:
            import google.generativeai as genai
            model = "models/text-embedding-004"
            resp = genai.embed_content(
                model=model,
                content=clean,
                task_type="retrieval_document"
            )
            if resp and "embedding" in resp:
                emb = resp["embedding"]
                # L2 normalize
                norm = math.sqrt(sum(x * x for x in emb))
                if norm > 0:
                    return [round(x / norm, 6) for x in emb]
        except Exception:
            pass  # Fall through to deterministic vector

    return _deterministic_semantic_vector(clean, dim=128)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec_a or not vec_b:
        return 0.0

    # Pad or truncate if dimensions differ
    min_len = min(len(vec_a), len(vec_b))
    dot = sum(vec_a[i] * vec_b[i] for i in range(min_len))
    norm_a = math.sqrt(sum(x * x for x in vec_a[:min_len]))
    norm_b = math.sqrt(sum(y * y for y in vec_b[:min_len]))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def index_knowledge_base(force_reindex: bool = False) -> Dict[str, Any]:
    """
    Indexes all 46 interior categories into the KNOWLEDGE_VECTORS table.
    Ensures safe, idempotent population.
    """
    database.init_db()
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM KNOWLEDGE_VECTORS;")
        existing_count = cursor.fetchone()[0]

        if existing_count >= 46 and not force_reindex:
            return {"status": "already_indexed", "count": existing_count}

        if force_reindex:
            with conn:
                cursor.execute("DELETE FROM KNOWLEDGE_VECTORS;")

        catalog = india_interior_knowledge.get_all_categories()
        indexed_count = 0
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with conn:
            for entry in catalog:
                chunk_id = f"KNOW-CHUNK-{entry['category_number']:04d}"
                text_to_embed = f"{entry['title']}\nTopic: {entry['topic']}\nCategory: {entry['category_name']}\n{entry['content']}\nSource: {entry['verified_source']}"
                vec = generate_embedding(text_to_embed)
                vec_json = json.dumps(vec)

                cursor.execute("""
                INSERT OR REPLACE INTO KNOWLEDGE_VECTORS (
                    chunk_id, category_number, category_name, topic, title,
                    source_type, verified_source, region, content, embedding_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    chunk_id,
                    entry["category_number"],
                    entry["category_name"],
                    entry["topic"],
                    entry["title"],
                    entry["source_type"],
                    entry["verified_source"],
                    entry["region"],
                    entry["content"],
                    vec_json,
                    now_str
                ))
                indexed_count += 1

        return {"status": "success", "count": indexed_count}
    finally:
        conn.close()


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 3,
    min_confidence: float = 0.20
) -> List[Dict[str, Any]]:
    """
    Retrieves the top-k most semantically relevant knowledge chunks for a query.
    Returns chunk details along with similarity score and citation badge.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    # Ensure knowledge base is indexed
    index_knowledge_base(force_reindex=False)

    q_vec = generate_embedding(clean_query)

    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT chunk_id, category_number, category_name, topic, title,
               source_type, verified_source, region, content, embedding_json
        FROM KNOWLEDGE_VECTORS;
        """)
        rows = cursor.fetchall()
        scored_chunks = []

        for r in rows:
            emb_json = r["embedding_json"]
            if not emb_json:
                continue
            chunk_vec = json.loads(emb_json)
            sim = cosine_similarity(q_vec, chunk_vec)

            # Keyword boost for direct topic or term matches
            q_lower = clean_query.lower()
            topic_lower = (r["topic"] or "").lower()
            title_lower = (r["title"] or "").lower()
            content_lower = (r["content"] or "").lower()

            if topic_lower in q_lower or q_lower in topic_lower:
                sim += 0.15
            if any(w in title_lower for w in q_lower.split() if len(w) > 3):
                sim += 0.08
            if any(w in content_lower for w in q_lower.split() if len(w) > 4):
                sim += 0.05

            if sim >= min_confidence:
                citation = f"[Source: {r['verified_source']}]"
                scored_chunks.append({
                    "chunk_id": r["chunk_id"],
                    "category_number": r["category_number"],
                    "category_name": r["category_name"],
                    "topic": r["topic"],
                    "title": r["title"],
                    "source_type": r["source_type"],
                    "verified_source": r["verified_source"],
                    "region": r["region"],
                    "content": r["content"],
                    "similarity_score": round(sim, 4),
                    "citation": citation
                })

        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:top_k]
    finally:
        conn.close()


def generate_rag_response(
    query: str,
    customer_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a grounded, professional English interior design response
    using retrieved knowledge base chunks and verified source citations.
    """
    clean_q = query.strip()
    chunks = retrieve_relevant_chunks(clean_q, top_k=3)

    if not chunks:
        # Out of domain / Low confidence fallback
        fallback_msg = (
            "Thank you for your question. While I can provide general interior guidance, "
            "for specific technical execution or bespoke SHA Interface Interiors details, "
            "our senior design team at our Miyapur office will be pleased to assist you directly.\n\n"
            f"You can choose a convenient appointment between 2:00 PM and 5:00 PM using our booking link:\n"
            f"{business_config.GOOGLE_CALENDAR_BOOKING_LINK}"
        )
        return {
            "answer": fallback_msg,
            "citations": ["[Source: SHA Business Policy]"],
            "retrieved_chunks": [],
            "confidence": 0.0,
            "is_english_only": True
        }

    # Grounded synthesis
    top_score = chunks[0]["similarity_score"]
    citations = list({c["citation"] for c in chunks})

    # Prepare grounding text
    context_blocks = []
    for idx, c in enumerate(chunks, 1):
        context_blocks.append(
            f"--- CHUNK {idx} ---\n"
            f"Title: {c['title']}\n"
            f"Source: {c['verified_source']} ({c['source_type']})\n"
            f"Region: {c['region']}\n"
            f"Details: {c['content']}"
        )
    combined_context = "\n\n".join(context_blocks)

    if ai_service.is_gemini_available():
        prompt = f"""You are the senior architectural & interior design AI consultant for SHA Interface Interiors.
Provide an authoritative, clear, and helpful response to the customer's question.

CUSTOMER QUESTION:
\"\"\"{clean_q}\"\"\"

{f"CUSTOMER CONTEXT: {customer_context}" if customer_context else ""}

VERIFIED RETRIEVED KNOWLEDGE:
{combined_context}

OFFICIAL SHA BUSINESS RULES:
- Office name: Miyapur office (NEVER Hyderabad Studio)
- Customer appointment hours: strictly 2:00 PM to 5:00 PM IST, Monday through Sunday.
- Booking Link: {business_config.GOOGLE_CALENDAR_BOOKING_LINK}
- Quotation Policy: Custom quotations require floor plan review and design consultation.
- 3D Design Policy: Bespoke 3D renders are developed after formal project engagement.

MANDATORY RULES:
1. Provide the response in clear, professional ENGLISH ONLY.
2. Ground your technical guidance on the verified chunks above.
3. Explicitly cite the verified sources in brackets, e.g. [Source: BIS IS 710:2010].
4. If the customer asks about visiting or appointments, provide the Miyapur office details and booking link.
"""
        res = ai_service.generate_content(prompt, temperature=0.2, max_output_tokens=500)
        if res.get("success") and res.get("text"):
            answer = res["text"].strip()
            return {
                "answer": answer,
                "citations": citations,
                "retrieved_chunks": chunks,
                "confidence": top_score,
                "is_english_only": True
            }

    # Deterministic Grounded Generation (Zero-downtime offline fallback)
    primary = chunks[0]
    sec = chunks[1] if len(chunks) > 1 else None

    ans_lines = [
        f"**{primary['title']}**",
        f"{primary['content']}",
        f"\n**Verified Standard:** {primary['citation']}"
    ]
    if sec and sec["category_number"] != primary["category_number"]:
        ans_lines.extend([
            f"\n**Related Recommendation - {sec['title']}:**",
            f"{sec['content']}",
            f"{sec['citation']}"
        ])

    # If query inquires about visit/consultation/office
    q_low = clean_q.lower()
    if any(k in q_low for k in ["visit", "meet", "office", "appointment", "schedule", "miyapur", "consult"]):
        ans_lines.extend([
            "\n**Visiting SHA Interface Interiors:**",
            "We would be delighted to welcome you to our Miyapur office. Consultations are available from 2:00 PM to 5:00 PM, all seven days of the week.",
            f"You can choose your preferred slot using our booking link:\n{business_config.GOOGLE_CALENDAR_BOOKING_LINK}"
        ])

    answer = "\n".join(ans_lines)

    return {
        "answer": answer,
        "citations": citations,
        "retrieved_chunks": chunks,
        "confidence": top_score,
        "is_english_only": True
    }
