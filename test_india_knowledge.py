"""
test_india_knowledge.py - Verification Suite for India-Wide Interior Design Knowledge Base
Tests:
- Verifies exact 46 categories coverage
- Validates verified sources and regional metadata
- Strict separation between general interior knowledge and SHA internal policies
- Search retrieval and relevance scoring
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import india_interior_knowledge


class TestIndiaInteriorKnowledge(unittest.TestCase):
    """Test suite for India-wide interior knowledge catalog."""

    def test_01_all_46_categories_exist(self):
        """Verify the knowledge base contains all 46 structured categories."""
        catalog = india_interior_knowledge.get_all_categories()
        self.assertEqual(len(catalog), 46, "Knowledge base must have all 46 categories")

        # Verify sequential numbering 1 to 46
        numbers = [entry["category_number"] for entry in catalog]
        self.assertEqual(numbers, list(range(1, 47)))

    def test_02_field_completeness_and_sources(self):
        """Verify all entries contain valid content, verified sources, and regional tags."""
        for entry in india_interior_knowledge.get_all_categories():
            self.assertIn("category_number", entry)
            self.assertIn("category_name", entry)
            self.assertIn("topic", entry)
            self.assertIn("title", entry)
            self.assertIn("content", entry)
            self.assertIn("verified_source", entry)
            self.assertIn("region", entry)
            self.assertIn("source_type", entry)

            # Ensure fields are non-empty
            self.assertTrue(len(entry["content"]) > 30)
            self.assertTrue(len(entry["verified_source"]) > 3)

    def test_03_separation_of_general_standards_and_sha_policies(self):
        """Verify general interior facts are strictly separated from SHA internal business policies."""
        catalog = india_interior_knowledge.get_all_categories()

        # Categories 1 to 45 must be General Interior Standard
        for entry in catalog[:45]:
            self.assertEqual(entry["source_type"], "General Interior Standard")
            self.assertNotIn("Miyapur office", entry["title"])

        # Category 46 must be SHA Internal Business Policy
        sha_policy = catalog[45]
        self.assertEqual(sha_policy["category_number"], 46)
        self.assertEqual(sha_policy["source_type"], "SHA Internal Business Policy")
        self.assertIn("Miyapur office", sha_policy["content"])
        self.assertIn("2:00 PM to 5:00 PM", sha_policy["content"])
        self.assertIn("https://calendar.app.google/DMb8MRbZBz97gYbc8", sha_policy["content"])

    def test_04_search_functionality(self):
        """Verify search finds relevant items for technical queries."""
        # Query for BWP
        bwp_res = india_interior_knowledge.search_knowledge("BWP plywood")
        self.assertTrue(len(bwp_res) > 0)
        self.assertEqual(bwp_res[0]["topic"], "BWP Marine Plywood")

        # Query for Chimney
        chimney_res = india_interior_knowledge.search_knowledge("kitchen chimney suction duct")
        self.assertTrue(len(chimney_res) > 0)
        self.assertEqual(chimney_res[0]["topic"], "Chimney & Ventilation")

        # Query for Appointment / Miyapur
        sha_res = india_interior_knowledge.search_knowledge("Miyapur appointment timings")
        self.assertTrue(len(sha_res) > 0)
        self.assertEqual(sha_res[0]["category_number"], 46)


if __name__ == "__main__":
    unittest.main()
