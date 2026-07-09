"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";
import { EditorialDigestView } from "@/components/editorial/editorial-digest";

type EditorialDigest = {
  id: string;
  period: string;
  title: string;
  subtitle: string;
  executive_summary: string[];
  top_story: any;
  breaking_findings: any[];
  practice_impact: string[];
  controversies: any[];
  research_trends: any[];
  papers: any[];
  total_papers_reviewed: number;
  reading_time_minutes: number;
};

export default function EditorialPage() {
  const [digest, setDigest] = useState<EditorialDigest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<"daily" | "weekly">("daily");

  useEffect(() => {
    fetchEditorial(period);
  }, [period]);

  async function fetchEditorial(p: string) {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/editorial/${p}`);
      if (!res.ok) throw new Error(`Failed: ${res.statusText}`);
      setDigest(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">ENT Editorial Digest</h1>
            <p className="text-sm text-muted-foreground">
              AI-curated evidence-based review for ENT specialists
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={period === "daily" ? "default" : "outline"}
              size="sm"
              onClick={() => setPeriod("daily")}
            >
              Today
            </Button>
            <Button
              variant={period === "weekly" ? "default" : "outline"}
              size="sm"
              onClick={() => setPeriod("weekly")}
            >
              Week
            </Button>
          </div>
        </div>

        {isLoading && <LoadingState count={5} />}

        {error && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
              <Button variant="outline" size="sm" className="mt-2" onClick={() => fetchEditorial(period)}>
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {digest && <EditorialDigestView digest={digest} />}
      </div>
    </ErrorBoundary>
  );
}
