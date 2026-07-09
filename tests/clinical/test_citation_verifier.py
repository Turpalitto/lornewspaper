"""Tests for CitationVerifier."""

from __future__ import annotations

from clinical_assistant.services.citation_verifier import CitationVerifier


class TestCitationVerifier:
    def setup_method(self):
        self.verifier = CitationVerifier()

    def test_register_and_verify_exact_match(self):
        text = "We recommend amoxicillin 500 mg three times daily for 7 days."
        source_id = "guideline-001"
        h = self.verifier.register_text(text, source_id)

        result = self.verifier.verify_citation(text)
        assert result["verified"] is True
        assert result["confidence"] == 1.0
        assert result["source_id"] == source_id

    def test_verify_unknown_text(self):
        result = self.verifier.verify_citation("Unknown text that was never registered")
        assert result["verified"] is False
        assert result["source_id"] is None

    def test_multiple_sources(self):
        self.verifier.register_text("Text A", "source-a")
        self.verifier.register_text("Text B", "source-b")

        r1 = self.verifier.verify_citation("Text A")
        assert r1["source_id"] == "source-a"

        r2 = self.verifier.verify_citation("Text B")
        assert r2["source_id"] == "source-b"
