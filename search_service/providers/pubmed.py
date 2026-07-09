"""PubMed provider via NCBI E-utilities.

Flow:
  * ``esearch.fcgi`` resolves a query (optionally date-scoped) to a list of
    PMIDs.
  * ``efetch.fcgi`` (retmode=json, v2.0) returns structured metadata including
    abstract, authors, keywords, MeSH and article IDs for those PMIDs.

PubMed has no native batch abstract endpoint, so we always fetch full records
for the resolved IDs.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict

from search_service.base import BaseProvider
from search_service.config import ProviderCapabilities
from search_service.models import Article


class _ESearchResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    esearchresult: dict[str, Any]


class _EFetchResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    result: dict[str, Any]


_YEAR_RE = re.compile(r"(\d{4})")

# Cap requested page sizes so a single call can't exhaust the API quota or
# blow up response/memory size.
_MAX_LIMIT = 100


class PubMedProvider(BaseProvider):
    name = "pubmed"
    capabilities = ProviderCapabilities()

    # -- public interface --------------------------------------------------
    async def search(self, query: str, limit: int = 20) -> list[Article]:
        ids = await self._esearch(query, limit)
        return await self._fetch_articles(ids)

    async def search_by_date(
        self,
        query: str,
        from_year: int | None = None,
        to_year: int | None = None,
        limit: int = 20,
    ) -> list[Article]:
        ids = await self._esearch(
            query, limit, datetype="pdat", from_year=from_year, to_year=to_year
        )
        return await self._fetch_articles(ids)

    async def search_by_pmid(self, pmid: str) -> Article | None:
        articles = await self._fetch_articles([pmid])
        return articles[0] if articles else None

    async def get_metadata(self, identifier: str) -> Article | None:
        if identifier.isdigit():
            ids = [identifier]
        else:
            ids = await self._esearch(identifier, 1)
        articles = await self._fetch_articles(ids)
        return articles[0] if articles else None

    async def get_abstract(self, identifier: str) -> str | None:
        article = await self.get_metadata(identifier)
        return article.abstract if article else None

    async def healthcheck(self) -> bool:
        try:
            await self._request_raw(
                "GET",
                "/einfo.fcgi",
                params={"db": "pubmed", "retmode": "json"},
                timeout=min(self.config.timeout, 5.0),
            )
            return True
        except Exception:
            return False

    # -- internals ---------------------------------------------------------
    async def _esearch(
        self,
        query: str,
        limit: int,
        datetype: str | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
    ) -> list[str]:
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max(1, min(limit, _MAX_LIMIT)),
        }
        if datetype:
            params["datetype"] = datetype
            # Use full dates: PubMed requires a parseable date, and a bare year
            # is ambiguous. Open-ended bounds are simply omitted.
            if from_year:
                params["mindate"] = f"{from_year}-01-01"
            if to_year:
                params["maxdate"] = f"{to_year}-12-31"
        result = await self._fetch(
            endpoint="/esearch.fcgi",
            params=params,
            response_model=_ESearchResponse,
            map_fn=lambda m: list(m.esearchresult.get("idlist", [])),
            query=query,
        )
        return result

    async def _fetch_articles(self, ids: list[str]) -> list[Article]:
        if not ids:
            return []
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
            "rettype": "abstract",
        }
        articles = await self._fetch(
            endpoint="/efetch.fcgi",
            params=params,
            response_model=_EFetchResponse,
            map_fn=lambda m: self._map_fetch(m),
            query=",".join(ids),
        )
        return articles

    def _map_fetch(self, data: _EFetchResponse) -> list[Article]:
        result = data.result
        uids = result.get("uids", [])
        return [self._record_to_article(result[uid], uid) for uid in uids if uid in result]

    def _record_to_article(self, rec: dict[str, Any], uid: str) -> Article:
        authors = [a["name"] for a in rec.get("authors", []) if a.get("name")]
        doi = pmid = pmcid = None
        for aid in rec.get("articleids", []):
            itype = aid.get("idtype")
            val = aid.get("value")
            if itype == "doi":
                doi = val
            elif itype == "pubmed":
                pmid = val
            elif itype == "pmc":
                pmcid = val
        if pmid is None:
            pmid = uid

        abstract = rec.get("abstracttext")
        if isinstance(abstract, list):
            abstract = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in abstract
            )
        elif abstract is not None:
            abstract = str(abstract)

        pubdate = rec.get("pubdate", "")
        year_match = _YEAR_RE.search(pubdate)
        year = int(year_match.group(1)) if year_match else None

        pdf_url = self._extract_pdf(rec)

        return Article(
            title=rec.get("title"),
            authors=authors,
            journal=rec.get("fulljournalname") or rec.get("source"),
            year=year,
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            abstract=abstract,
            keywords=list(rec.get("keywords", []) or []),
            mesh_terms=list(rec.get("meshterms", []) or []),
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
            pdf_url=pdf_url,
            source=self.name,
            language=self._first(rec.get("lang")),
            publication_type=list(rec.get("pubtype", []) or []),
            publisher=rec.get("publishername"),
            volume=rec.get("volume"),
            issue=rec.get("issue"),
            pages=rec.get("pages"),
            id=None,
            provenance=[self.name],
        )

    @staticmethod
    def _extract_pdf(rec: dict[str, Any]) -> str | None:
        for entry in rec.get("fulltexturl", []) or []:
            if entry.get("content") == "pdf" and entry.get("url"):
                return entry["url"]
        return None

    @staticmethod
    def _first(value: Any) -> str | None:
        if isinstance(value, list):
            return value[0] if value else None
        return value
