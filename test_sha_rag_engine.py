"""
test_sha_rag_engine.py - Verification Suite for SHA-Specific RAG System
Tests:
- Knowledge base vector indexing in SQLite
- Pure Python cosine similarity calculation
- Semantic chunk retrieval with metadata & citations
- Grounded RAG answer generation with English-only enforcement
- SHA appointment rules and booking link inclusion
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database
import sha_rag_engine
import business_config


class TestShaRagEngine(unittest.TestCase):
    """Test suite for SHA-specific RAG system."""

    @classmethod
    def setUpClass(cls):
        database.init_db()
        # Ensure knowledge base is indexed
        cls.index_result = sha_rag_engine.index_knowledge_base(force_reindex=False)

    def test_01_knowledge_base_indexing(self):
        """Verify all 46 categories are properly indexed in the KNOWLEDGE_VECTORS table."""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM KNOWLEDGE_VECTORS;")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertGreaterEqual(count, 46)

    def test_02_cosine_similarity(self):
        """Verify vector cosine similarity logic."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]
        vec4 = [-1.0, 0.0, 0.0]

        self.assertAlmostEqual(sha_rag_engine.cosine_similarity(vec1, vec2), 1.0)
        self.assertAlmostEqual(sha_rag_engine.cosine_similarity(vec1, vec3), 0.0)
        self.assertAlmostEqual(sha_rag_engine.cosine_similarity(vec1, vec4), -1.0)

    def test_03_chunk_retrieval_and_citations(self):
        """Verify semantic retrieval returns relevant chunks and verified source citations."""
        query = "What is the difference between BWP marine plywood and commercial plywood?"
        chunks = sha_rag_engine.retrieve_relevant_chunks(query, top_k=2)

        self.assertTrue(len(chunks) > 0)
        top_chunk = chunks[0]
        self.assertIn("verified_source", top_chunk)
        self.assertIn("citation", top_chunk)
        self.assertTrue(top_chunk["citation"].startswith("[Source:"))
        # Expect BWP (IS:710) or Commercial (IS:303) in top retrieved results
        top_cats = [c["category_number"] for c in chunks]
        self.assertTrue(1 in top_cats or 2 in top_cats)

    def test_04_rag_grounded_response_generation(self):
        """Verify RAG answers are generated in English with citations."""
        query = "Can you recommend durable countertop materials that resist turmeric stains?"
        res = sha_rag_engine.generate_rag_response(query)

        self.assertTrue(res["is_english_only"])
        self.assertTrue(len(res["citations"]) > 0)
        self.assertTrue(len(res["answer"]) > 50)
        # Check citation presence
        self.assertTrue(any("[Source:" in c for c in res["citations"]))

    def test_05_rag_office_appointment_compliance(self):
        """Verify that appointment or office queries include Miyapur office, 2-5 PM, and the booking link."""
        query = "When can I visit your office to discuss my 3BHK interior project?"
        res = sha_rag_engine.generate_rag_response(query)

        ans = res["answer"]
        self.assertIn("Miyapur office", ans)
        self.assertNotIn("Hyderabad Studio", ans)
        self.assertIn(business_config.GOOGLE_CALENDAR_BOOKING_LINK, ans)


if __name__ == "__main__":
    unittest.main()
