#!/usr/bin/env python3
"""Seed medical ontologies (ICD-10, ATC, MeSH) from local data files.

Usage:
    python scripts/seed_ontologies.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("Medical Ontology Seed Script")
    print("=" * 50)
    print("Expected data files:")
    print("  data/ontologies/icd10_ru.json — Russian ICD-10 codes")
    print("  data/ontologies/atc_index.json — ATC classification")
    print("  data/ontologies/mesh_ru.json — Russian MeSH terms")
    print()
    print("To import ontologies, place the data files in data/ontologies/")
    print("and run this script.")
    print()
    print("Format expected:")
    print("  icd10_ru.json: [{\"code\": \"J18.9\", \"name\": \"Пневмония неуточненная\", ...}]")
    print("  atc_index.json: [{\"code\": \"J01CA04\", \"name\": \"Amoxicillin\", ...}]")
    print("  mesh_ru.json: [{\"id\": \"D011014\", \"term_ru\": \"Пневмония\", ...}]")


if __name__ == "__main__":
    main()
