"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";

type TrendTopic = { name: string; description: string; growth_rate: number; paper_count: number; momentum: string; emerging: boolean };

const momentumColors: Record<string, string> = {
  exploding: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
  growing: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  stable: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
  declining: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100",
};

export default function TrendingPage() {
  const [trending, setTrending] = useState<TrendTopic[]>([]);
  const [emerging, setEmerging] = useState<TrendTopic[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/v1/discovery/trending").then(r => r.json()),
      fetch("/api/v1/discovery/emerging").then(r => r.json()),
    ]).then(([t, e]) => { setTrending(t); setEmerging(e); }).finally(() => setIsLoading(false));
  }, []);

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <Link href="/discovery" className="text-sm text-muted-foreground hover:text-foreground">&larr; Discovery</Link>
          <h1 className="text-2xl font-bold mt-2">Trending Topics</h1>
        </div>
        {isLoading && <LoadingState count={3} />}
        {emerging.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3">🚀 Emerging</h2>
            <div className="grid gap-3">
              {emerging.map(t => (
                <Card key={t.name} className="border-green-200 dark:border-green-800">
                  <CardContent className="pt-4 flex justify-between items-center">
                    <div>
                      <p className="font-medium">{t.name}</p>
                      <p className="text-xs text-muted-foreground">{t.description}</p>
                    </div>
                    <div className="text-right">
                      <span className={`text-xs px-2 py-1 rounded ${momentumColors[t.momentum] || ""}`}>
                        +{t.growth_rate}%
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}
        {trending.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3">📈 Trending</h2>
            <div className="grid gap-3">
              {trending.map(t => (
                <Card key={t.name}>
                  <CardContent className="pt-4 flex justify-between items-center">
                    <div>
                      <p className="font-medium">{t.name}</p>
                      <p className="text-xs text-muted-foreground">{t.paper_count} papers</p>
                    </div>
                    <Badge variant="secondary">{t.momentum}</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}
      </div>
    </ErrorBoundary>
  );
}
