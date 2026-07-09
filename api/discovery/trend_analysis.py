"""Trend analysis — detect new diseases, procedures, devices, drugs, surgical techniques."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from api.discovery.models import DiscoveryItem

# Procedure detection patterns
_PROCEDURE_PATTERNS = [
    (r"(?:novel|new|modified|innovative)\s+(\w+(?:\s+\w+)?)\s+(?:technique|procedure|approach|method)", "procedure"),
    (r"(?:endoscopic|robotic|laser|microscopic)\s+(\w+(?:\s+\w+)?)\s+(?:surgery|resection|repair)", "technique"),
    (r"(?:transoral|transnasal|transcanal)\s+(\w+(?:\s+\w+)?)\s+(?:approach|surgery|access)", "approach"),
]

# Device detection
_DEVICE_PATTERNS = [
    (r"(?:novel|new)\s+(\w+(?:\s+\w+)?)\s+(?:device|implant|prosthesis|sensor)", "device"),
    (r"(?:implantable|wearable|smart)\s+(\w+(?:\s+\w+)?)", "device"),
]

# Drug detection
_DRUG_PATTERNS = [
    (r"(?:novel|new)\s+(\w+(?:\s+\w+)?)\s+(?:drug|therapeutic|therapy|treatment|agent)", "drug"),
    (r"(?:first-in-class|first-line)\s+(\w+(?:\s+\w+)?)", "drug"),
]


class TrendAnalyzer:
    """Analyze discovery items for emerging trends."""

    def analyze(self, items: list[DiscoveryItem]) -> dict[str, list[str]]:
        """Analyze items for new procedures, devices, drugs, and techniques."""
        return {
            "new_procedures": self._find_new_procedures(items),
            "new_devices": self._find_new_devices(items),
            "new_drugs": self._find_new_drugs(items),
            "new_techniques": self._find_new_techniques(items),
            "new_diseases": self._find_new_diseases(items),
        }

    def _find_new_procedures(self, items: list[DiscoveryItem]) -> list[str]:
        """Detect mentions of novel procedures."""
        found: list[str] = []
        for item in items:
            text = f"{item.title} {item.abstract}"
            for pattern, _ in _PROCEDURE_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    found.append(match.group(0).strip()[:100])
        return found[:10]

    def _find_new_devices(self, items: list[DiscoveryItem]) -> list[str]:
        """Detect mentions of novel devices."""
        found: list[str] = []
        for item in items:
            text = f"{item.title} {item.abstract}"
            for pattern, _ in _DEVICE_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    found.append(match.group(0).strip()[:100])
        return found[:10]

    def _find_new_drugs(self, items: list[DiscoveryItem]) -> list[str]:
        """Detect mentions of novel drugs or therapies."""
        found: list[str] = []
        for item in items:
            text = f"{item.title} {item.abstract}"
            for pattern, _ in _DRUG_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    found.append(match.group(0).strip()[:100])
        return found[:10]

    def _find_new_techniques(self, items: list[DiscoveryItem]) -> list[str]:
        """Detect mentions of new surgical techniques."""
        found: list[str] = []
        keywords = [
            "robotic surgery", "robot-assisted", "navigation system",
            "image-guided", "3d-printed", "patient-specific",
            "augmented reality", "virtual reality", "simulation",
            "laser-assisted", "ultrasound-guided",
        ]
        for item in items:
            text = f"{item.title} {item.abstract}".lower()
            for kw in keywords:
                if kw in text:
                    found.append(kw)
        return list(set(found))[:10]

    def _find_new_diseases(self, items: list[DiscoveryItem]) -> list[str]:
        """Detect mentions of emerging disease areas."""
        found: list[str] = []
        keywords = [
            "long COVID", "post-COVID", "COVID-19 otologic",
            "mRNA vaccine", "AAV", "gene editing",
            "organoid", "3D culture", "tissue engineering",
        ]
        for item in items:
            text = f"{item.title} {item.abstract}".lower()
            for kw in keywords:
                if kw in text:
                    found.append(kw)
        return list(set(found))[:10]
