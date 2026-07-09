"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";
import { EmptyState } from "@/components/shared/empty-state";
import { cn } from "@/lib/utils";

type Recommendation = {
  id: string;
  text_ru: string;
  strength: string;
  evidence_level: string;
  contraindications: string[];
};

type GuidelineSection = {
  id: string;
  heading: string;
  content: string;
  recommendations: Recommendation[];
};

type Guideline = {
  id: string;
  title_ru: string;
  source: string;
  version: string;
  sections: GuidelineSection[];
  recommendations: Recommendation[];
};

type SearchResult = {
  items: Guideline[];
  total: number;
};

const strengthColor: Record<string, string> = {
  strong: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  conditional: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
  not_recommended: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
  open: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100",
};

export default function GuidelinesPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch() {
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const res = await fetch("/api/v1/clinical/guidelines/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), top_k: 10 }),
      });
      if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">Clinical Guidelines</h1>
          <p className="text-muted-foreground text-sm">
            Search evidence-based clinical guidelines and recommendations
          </p>
        </div>

        <div className="flex gap-2">
          <Input
            placeholder="Search by diagnosis, symptom, or drug..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="flex-1"
            aria-label="Search guidelines"
          />
          <Button onClick={handleSearch} disabled={isLoading || !query.trim()}>
            {isLoading ? "Searching..." : "Search"}
          </Button>
        </div>

        {isLoading && <LoadingState count={3} />}

        {error && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {results && results.items.length === 0 && (
          <EmptyState
            title="No guidelines found"
            description={`No guidelines matching "${query}". Try a different search term.`}
          />
        )}

        {results && results.items.length > 0 && (
          <div className="space-y-6">
            <p className="text-sm text-muted-foreground">
              {results.total} guideline{results.total !== 1 ? "s" : ""} found
            </p>
            {results.items.map((guideline) => (
              <GuidelineCard key={guideline.id} guideline={guideline} />
            ))}
          </div>
        )}

        {!hasSearched && !isLoading && (
          <p className="text-center text-muted-foreground py-12">
            Enter a diagnosis, symptom, or drug name to search clinical guidelines
          </p>
        )}
      </div>
    </ErrorBoundary>
  );
}

function GuidelineCard({ guideline }: { guideline: Guideline }) {
  const [expanded, setExpanded] = useState(false);
  const topRecs = guideline.recommendations.slice(0, 3);
  const hasMore = guideline.recommendations.length > 3;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-lg">
              <Link
                href={`/guidelines/${guideline.id}`}
                className="hover:text-primary transition-colors"
              >
                {guideline.title_ru || "Untitled Guideline"}
              </Link>
            </CardTitle>
            <div className="flex gap-2 text-xs text-muted-foreground">
              <Badge variant="secondary">{guideline.source}</Badge>
              {guideline.version && <span>v{guideline.version}</span>}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          {topRecs.map((rec) => (
            <RecommendationRow key={rec.id} rec={rec} />
          ))}
        </div>
        {hasMore && (
          <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)}>
            {expanded
              ? "Show less"
              : `Show ${guideline.recommendations.length - 3} more recommendations`}
          </Button>
        )}
        {expanded &&
          guideline.recommendations.slice(3).map((rec) => (
            <RecommendationRow key={rec.id} rec={rec} />
          ))}
      </CardContent>
    </Card>
  );
}

function RecommendationRow({ rec }: { rec: Recommendation }) {
  return (
    <div className="border-l-2 border-primary/30 pl-3 py-1">
      <p className="text-sm">{rec.text_ru || "(No text)"}</p>
      <div className="flex gap-2 mt-1">
        <span className={cn("text-xs px-1.5 py-0.5 rounded", strengthColor[rec.strength] || "")}>
          {rec.strength}
        </span>
        {rec.evidence_level && (
          <span className="text-xs text-muted-foreground">
            Evidence: {rec.evidence_level}
          </span>
        )}
      </div>
    </div>
  );
}
