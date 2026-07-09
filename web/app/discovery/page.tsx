"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";

type DiscoveryItem = {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  doi: string;
  source: string;
  discovery_strategy: string;
  citation_count: number;
};

type TrendTopic = {
  name: string;
  growth_rate: number;
  paper_count: number;
  momentum: string;
  emerging: boolean;
};

type Author = {
  name: string;
  paper_count: number;
  recent_papers: string[];
};

type Journal = {
  name: string;
  impact_factor: number;
  papers_this_period: number;
};

type DiscoveryResult = {
  total_discovered: number;
  strategies_used: string[];
  items: DiscoveryItem[];
  new_authors: Author[];
  top_journals: Journal[];
  trending_topics: TrendTopic[];
  emerging_topics: TrendTopic[];
};

const strategyLabels: Record<string, string> = {
  keyword_search: "Keyword",
  citation_expansion: "Citations",
  reference_expansion: "References",
  author_tracking: "Authors",
  journal_tracking: "Journals",
  trend_detection: "Trends",
};

const momentumColors: Record<string, string> = {
  exploding: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
  growing: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  stable: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
  declining: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100",
};

export default function DiscoveryPage() {
  const [discovery, setDiscovery] = useState<DiscoveryResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { fetchDiscovery(); }, []);

  async function fetchDiscovery() {
    setIsLoading(true); setError(null);
    try {
      const res = await fetch("/api/v1/discovery/today");
      if (!res.ok) throw new Error(`Failed: ${res.statusText}`);
      setDiscovery(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally { setIsLoading(false); }
  }

  return (
    <ErrorBoundary>
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">Content Discovery</h1>
            <p className="text-sm text-muted-foreground">
              Continuously discovering emerging ENT research
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/discovery/trending">
              <Button variant="outline" size="sm">Trending</Button>
            </Link>
            <Link href="/discovery/authors">
              <Button variant="outline" size="sm">Authors</Button>
            </Link>
            <Link href="/discovery/journals">
              <Button variant="outline" size="sm">Journals</Button>
            </Link>
          </div>
        </div>

        {isLoading && <LoadingState count={4} />}

        {error && (
          <Card><CardContent className="pt-6"><p className="text-destructive">{error}</p></CardContent></Card>
        )}

        {discovery && (
          <>
            {/* Stats bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-2xl font-bold">{discovery.total_discovered}</p>
                  <p className="text-xs text-muted-foreground">Papers Discovered</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-2xl font-bold">{discovery.strategies_used.length}</p>
                  <p className="text-xs text-muted-foreground">Strategies Active</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-2xl font-bold">{discovery.trending_topics.length}</p>
                  <p className="text-xs text-muted-foreground">Trending Topics</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-2xl font-bold">{discovery.new_authors.length}</p>
                  <p className="text-xs text-muted-foreground">Top Authors</p>
                </CardContent>
              </Card>
            </div>

            {/* Strategies used */}
            <div className="flex flex-wrap gap-2">
              {discovery.strategies_used.map((s) => (
                <Badge key={s} variant="secondary">
                  {strategyLabels[s] || s}
                </Badge>
              ))}
            </div>

            {/* Emerging topics */}
            {discovery.emerging_topics.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold mb-3">🚀 Emerging Topics</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {discovery.emerging_topics.map((t) => (
                    <Card key={t.name} className="border-green-200 dark:border-green-800">
                      <CardContent className="pt-4">
                        <p className="font-medium text-sm">{t.name}</p>
                        <div className="flex gap-2 mt-2">
                          <span className={`text-xs px-1.5 py-0.5 rounded ${momentumColors[t.momentum] || ""}`}>
                            {t.momentum} {t.growth_rate}%
                          </span>
                          <span className="text-xs text-muted-foreground">{t.paper_count} papers</span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </section>
            )}

            {/* Trending topics */}
            {discovery.trending_topics.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold mb-3">📈 Trending Topics</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {discovery.trending_topics.map((t) => (
                    <Card key={t.name}>
                      <CardContent className="pt-4">
                        <p className="font-medium text-sm">{t.name}</p>
                        <div className="flex gap-2 mt-2">
                          <span className={`text-xs px-1.5 py-0.5 rounded ${momentumColors[t.momentum] || ""}`}>
                            {t.momentum}
                          </span>
                          <span className="text-xs text-muted-foreground">{t.paper_count} papers</span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </section>
            )}

            {/* Top journals */}
            {discovery.top_journals.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold mb-3">🏛️ Top Journals</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {discovery.top_journals.map((j) => (
                    <Card key={j.name}>
                      <CardContent className="pt-4 flex justify-between items-center">
                        <p className="text-sm font-medium">{j.name}</p>
                        <div className="text-right text-xs text-muted-foreground">
                          <p>IF: {j.impact_factor}</p>
                          <p>{j.papers_this_period} papers</p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </ErrorBoundary>
  );
}
