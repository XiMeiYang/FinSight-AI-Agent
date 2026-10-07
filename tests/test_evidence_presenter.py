import unittest

from finsight_app.evidence_presenter import make_evidence_excerpt, present_results


class EvidencePresenterTests(unittest.TestCase):
    def test_prefers_matching_complete_sentence_and_does_not_mutate_text(self):
        source = "Alpha is stable. Demand risks include supply constraints. Margins improved."
        result = make_evidence_excerpt(source, "What risks affect demand?", 200)
        self.assertIn("Demand risks include supply constraints.", result["evidence_excerpt"])
        self.assertEqual(source, "Alpha is stable. Demand risks include supply constraints. Margins improved.")
        self.assertIn("risks", result["matched_terms"])
        self.assertFalse(result["excerpt_truncated"])

    def test_truncation_uses_word_boundaries_and_ellipsis(self):
        result = make_evidence_excerpt("Demand could be affected by customer concentration and rapidly changing market conditions.", "demand risks", 35)
        excerpt = result["evidence_excerpt"]
        self.assertTrue(result["excerpt_truncated"])
        self.assertTrue(excerpt.endswith("..."))
        self.assertNotRegex(excerpt[:-3], r"\w$-\w")
        self.assertLessEqual(len(excerpt), 35)

    def test_centered_window_never_starts_or_ends_inside_a_word(self):
        result = make_evidence_excerpt(
            "The company reports that demand risks include concentration and rapidly changing markets.",
            "demand risks", 42)
        excerpt = result["evidence_excerpt"]
        visible = excerpt.strip(". ")
        self.assertFalse(visible.startswith("em"))
        self.assertRegex(visible, r"[A-Za-z0-9]$")
        self.assertLessEqual(len(excerpt), 42)

    def test_drops_obvious_chunk_edge_fragments_when_context_exists(self):
        result = make_evidence_excerpt(
            "erifying blockchain exposure. Demand risks include supply constraints. The company monitors them.",
            "demand risks", 200)
        self.assertFalse(result["evidence_excerpt"].startswith("erifying"))
        self.assertNotIn("unable to i", result["evidence_excerpt"])
        quote_fragment = make_evidence_excerpt(
            'Risk Factors,” our filing is discussed here. Demand risks affect GPU sales.',
            'demand risks', 200)
        self.assertTrue(quote_fragment["evidence_excerpt"].startswith("Demand risks"))

    def test_single_sentence_edge_fragments_are_not_displayed(self):
        self.assertNotIn("erifying", make_evidence_excerpt(
            "erifying blockchain exposure", "blockchain")["evidence_excerpt"])
        self.assertNotIn("unable", make_evidence_excerpt(
            "unable to i", "unable")["evidence_excerpt"])
        self.assertNotIn(" p", make_evidence_excerpt(
            "application, p", "application")["evidence_excerpt"])

    def test_empty_and_long_sentence_are_safe(self):
        self.assertEqual(make_evidence_excerpt("   ", "risk", 20)["evidence_excerpt"], "")
        result = make_evidence_excerpt("risk " * 100, "risk", 20)
        self.assertTrue(result["excerpt_truncated"])
        self.assertLessEqual(len(result["evidence_excerpt"]), 20)
        long_token = make_evidence_excerpt("X" * 100, "risk", 10)
        self.assertLessEqual(len(long_token["evidence_excerpt"]), 10)

    def test_clipped_source_tail_has_explicit_ellipsis(self):
        result = make_evidence_excerpt("demand " + "market " * 60 + "financial results", "demand", 60)
        self.assertTrue(result["excerpt_truncated"])
        self.assertTrue(result["evidence_excerpt"].endswith("..."))

    def test_present_results_keeps_rank_and_uses_full_row_text(self):
        rows = [{"chunk_id": "c1", "text": "Revenue demand risk is material. " + "context " * 100,
                 "section_title": "Risk Factors"}]
        original = [{"chunk_id": "c1", "rank": 1, "rrf_score": 0.1, "bm25_rank": 2, "dense_rank": 1}]
        output = present_results(original, rows, "demand risk", 80)
        self.assertEqual(output[0]["rank"], 1)
        self.assertEqual(output[0]["bm25_rank"], 2)
        self.assertEqual(output[0]["dense_rank"], 1)
        self.assertEqual(output[0]["section_title"], "Risk Factors")
        self.assertIn("demand", output[0]["evidence_excerpt"].lower())
        self.assertNotIn("evidence_excerpt", original[0])

    def test_missing_ranked_chunk_fails_closed(self):
        with self.assertRaises(ValueError):
            present_results([{"chunk_id": "missing", "rank": 1}], [], "risk", 80)


if __name__ == "__main__":
    unittest.main()
