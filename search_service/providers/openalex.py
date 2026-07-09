"""OpenAlex REST API provider.

OpenAlex exposes a single ``/works`` endpoint. Search, date scoping and
identifier lookups are all expressed via ``search`` / ``filter`` query
parameters. The ``mailto`` parameter (from provider config) enables the
polite-pool with higher rate limits.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from search_service.base import BaseProvider
from search_service.config import ProviderCapabilities
from search_service.models import Article

# OpenAlex caps per-page at 200.
_MAX_LIMIT = 200


class _WorksResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[dict[str, Any]]
    meta: dict[str, Any] = {}


class OpenAlexProvider(BaseProvider):
    name = "openalex"
    capabilities = ProviderCapabilities()

    # -- public interface --------------------------------------------------
    async def search(self, query: str, limit: int = 20) -> list[Article]:
        params = self._base_params()
        params["search"] = query
        params["per-page"] = limit
        return await self._run(params, query)

    async def search_by_date(
        self,
        query: str,
        from_year: int | None = None,
        to_year: int | None = None,
        limit: int = 20,
    ) -> list[Article]:
        params = self._base_params()
        params["search"] = query
        params["per-page"] = max(1, min(limit, _MAX_LIMIT))
        filt = []
        if from_year:
            filt.append(f"from_publication_date:{from_year}-01-01")
        if to_year:
            filt.append(f"to_publication_date:{to_year}-12-31")
        if filt:
            params["filter"] = ",".join(filt)
        return await self._run(params, query)

    async def search_by_pmid(self, pmid: str) -> Article | None:
        params = self._base_params()
        params["filter"] = f"pmid:{pmid}"
        params["per-page"] = 1
        results = await self._run(params, f"pmid:{pmid}")
        return results[0] if results else None

    async def get_metadata(self, identifier: str) -> Article | None:
        params = self._base_params()
        if "/" in identifier:
            filt = f"doi:https://doi.org/{identifier.lstrip('/')}"
        elif identifier.isdigit():
            filt = f"pmid:{identifier}"
        else:
            params["search"] = identifier
            params["per-page"] = 1
            results = await self._run(params, identifier)
            return results[0] if results else None
        params["filter"] = filt
        params["per-page"] = 1
        results = await self._run(params, filt)
        return results[0] if results else None

    async def get_abstract(self, identifier: str) -> str | None:
        article = await self.get_metadata(identifier)
        return article.abstract if article else None

    async def healthcheck(self) -> bool:
        try:
            await self._request_raw(
                "GET",
                "/works",
                params={**self._base_params(), "per-page": 1},
                timeout=min(self.config.timeout, 5.0),
            )
            return True
        except Exception:
            return False

    # -- internals ---------------------------------------------------------
    def _base_params(self) -> dict[str, Any]:
        mailto = self.config.extra.get("mailto")
        fields = (
            "id,title,authorships,host_venue,publication_year,doi,ids,"
            "abstract_inverted_index,keywords,mesh,concepts,type,language,"
            "best_oa_location,oa_locations"
        )
        params: dict[str, Any] = {"select": fields}
        if mailto:
            params["mailto"] = mailto
        return params

    async def _run(self, params: dict[str, Any], query: str) -> list[Article]:
        return await self._fetch(
            endpoint="/works",
            params=params,
            response_model=_WorksResponse,
            map_fn=lambda m: [self._record_to_article(r) for r in m.results],
            query=query,
        )

    def _record_to_article(self, r: dict[str, Any]) -> Article:
        authors = [
            a.get("author", {}).get("display_name")
            for a in r.get("authorships", []) or []
            if a.get("author", {}).get("display_name")
        ]

        hv = r.get("host_venue") or {}
        ids = r.get("ids") or {}

        doi = r.get("doi") or ids.get("doi")
        pmid = ids.get("pmid")
        pmcid = ids.get("pmcid")

        best = r.get("best_oa_location") or {}
        pdf_url = best.get("pdf_url")
        if not pdf_url:
            for loc in r.get("oa_locations", []) or []:
                if loc.get("pdf_url"):
                    pdf_url = loc["pdf_url"]
                    break

        url = (
            best.get("landing_page_url")
            or r.get("id")
            or (f"https://doi.org/{doi}" if doi else None)
        )

        concepts = [
            c.get("display_name")
            for c in r.get("concepts", []) or []
            if c.get("display_name")
        ]
        mesh = [
            m.get("descriptor_name") or m.get("display_name")
            for m in r.get("mesh", []) or []
            if m.get("descriptor_name") or m.get("display_name")
        ]
        keywords = [
            k.get("display_name")
            for k in r.get("keywords", []) or []
            if k.get("display_name")
        ]

        return Article(
            title=r.get("title"),
            authors=authors,
            journal=hv.get("display_name"),
            year=r.get("publication_year"),
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            abstract=self._reconstruct_abstract(r.get("abstract_inverted_index")),
            keywords=keywords,
            mesh_terms=mesh or concepts,
            url=url,
            pdf_url=pdf_url,
            source=self.name,
            language=r.get("language"),
            publication_type=[r["type"]] if r.get("type") else [],
            publisher=hv.get("publisher"),
            volume=hv.get("volume"),
            issue=hv.get("issue"),
            pages=hv.get("pages"),
            license=best.get("license"),
            id=None,
            provenance=[self.name],
        )

    @staticmethod
    def _reconstruct_abstract(inverted_index: Any) -> str | None:
        if not isinstance(inverted_index, dict) or not inverted_index:
            return None
        length = max(max(positions) for positions in inverted_index.values()) + 1
        words: list[str | None] = [None] * length
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(w for w in words if w is not None)
