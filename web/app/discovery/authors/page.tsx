"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";

type Author = { name: string; paper_count: number; top_topics: string[]; recent_papers: string[] };

export default function AuthorsPage() {
  const [authors, setAuthors] = useState<Author[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/discovery/authors").then(r => r.json()).then(setAuthors).finally(() => setIsLoading(false));
  }, []);

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <Link href="/discovery" className="text-sm text-muted-foreground hover:text-foreground">&larr; Discovery</Link>
          <h1 className="text-2xl font-bold mt-2">Top ENT Researchers</h1>
        </div>
        {isLoading && <LoadingState count={5} />}
        <div className="grid gap-4">
          {authors.map(a => (
            <Card key={a.name}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{a.name}</CardTitle>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="secondary">{a.paper_count} papers</Badge>
                      {a.top_topics.map(t => <Badge key={t} variant="outline">{t}</Badge>)}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {a.recent_papers.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground font-semibold">Recent papers:</p>
                    {a.recent_papers.slice(0, 3).map((p, i) => (
                      <p key={i} className="text-sm line-clamp-1">{p}</p>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </ErrorBoundary>
  );
}
