"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";
import { DigestCard } from "@/components/digest/digest-card";
import { TopicCard } from "@/components/digest/topic-card";

type DigestItem = {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  doi: string;
  study_design: string;
  evidence_level: string;
  clinical_importance: number;
  summary_bullets: string[];
  tags: string[];
};

type Topic = {
  id: string;
  display_name: string;
  icon: string;
  paper_count: number;
  summary: string;
  items: DigestItem[];
};

type Digest = {
  id: string;
  period: string;
  title: string;
  topics: Topic[];
  total_papers: number;
  trending: DigestItem[];
};

export default function DigestPage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<"daily" | "weekly" | "monthly">("daily");

  useEffect(() => {
    fetchDigest(period);
  }, [period]);

  async function fetchDigest(p: string) {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/digest/${p}`);
      if (!res.ok) throw new Error(`Failed to load digest: ${res.statusText}`);
      setDigest(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ErrorBoundary>
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">ENT Literature Digest</h1>
            <p className="text-sm text-muted-foreground">
              Automatically curated evidence-based ENT publications
            </p>
          </div>
          <div className="flex gap-2">
            {(["daily", "weekly", "monthly"] as const).map((p) => (
              <Button
                key={p}
                variant={period === p ? "default" : "outline"}
                size="sm"
                onClick={() => setPeriod(p)}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </Button>
            ))}
          </div>
        </div>

        {isLoading && <LoadingState count={6} />}

        {error && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
              <Button variant="outline" size="sm" className="mt-2" onClick={() => fetchDigest(period)}>
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {digest && (
          <>
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {digest.total_papers} papers across {digest.topics.length} topics
              </p>
              <Link href="/digest/saved">
                <Button variant="ghost" size="sm">Saved Papers</Button>
              </Link>
            </div>

            {digest.trending.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold mb-4">🔥 Trending</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {digest.trending.slice(0, 3).map((item) => (
                    <DigestCard key={item.id} item={item} />
                  ))}
                </div>
              </section>
            )}

            <section>
              <h2 className="text-lg font-semibold mb-4">Topics</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {digest.topics.map((topic) => (
                  <TopicCard key={topic.id} topic={topic} />
                ))}
              </div>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-4">
                All Papers ({digest.total_papers})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {digest.trending.map((item) => (
                  <DigestCard key={item.id} item={item} />
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </ErrorBoundary>
  );
}
