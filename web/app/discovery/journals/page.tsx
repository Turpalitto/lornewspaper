"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";

type Journal = { name: string; impact_factor: number; papers_this_period: number };

export default function JournalsPage() {
  const [journals, setJournals] = useState<Journal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/discovery/journals").then(r => r.json()).then(setJournals).finally(() => setIsLoading(false));
  }, []);

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <Link href="/discovery" className="text-sm text-muted-foreground hover:text-foreground">&larr; Discovery</Link>
          <h1 className="text-2xl font-bold mt-2">Top ENT Journals</h1>
        </div>
        {isLoading && <LoadingState count={4} />}
        <div className="grid gap-4">
          {journals.map(j => (
            <Card key={j.name}>
              <CardContent className="pt-6 flex justify-between items-center">
                <div>
                  <p className="font-medium">{j.name}</p>
                  <div className="flex gap-2 mt-1">
                    <Badge variant="secondary">IF: {j.impact_factor}</Badge>
                    <Badge variant="outline">{j.papers_this_period} this period</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </ErrorBoundary>
  );
}
