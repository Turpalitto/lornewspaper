"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";
import { cn } from "@/lib/utils";

type CitationRecommendation = {
  text: string;
  strength: string;
  evidence_level: string;
  guideline: string;
  section: string;
};

type AskResponse = {
  answer: string;
  recommendations: CitationRecommendation[];
  sources: string[];
  confidence: number;
};

const strengthColor: Record<string, string> = {
  strong: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  conditional: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
  not_recommended: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
};

export function AskGuidelines() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasAsked, setHasAsked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk() {
    if (!question.trim()) return;
    setIsLoading(true);
    setError(null);
    setHasAsked(true);
    try {
      const res = await fetch("/api/v1/clinical/guidelines/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
      });
      if (!res.ok) throw new Error(`Request failed: ${res.statusText}`);
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        <div className="flex gap-2">
          <Input
            placeholder="Ask a clinical question..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            className="flex-1"
            aria-label="Clinical question"
          />
          <Button onClick={handleAsk} disabled={isLoading || !question.trim()}>
            {isLoading ? "Searching guidelines..." : "Ask Guidelines"}
          </Button>
        </div>

        {isLoading && <LoadingState count={2} />}

        {error && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {result && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Answer</CardTitle>
                  {result.confidence > 0 && (
                    <span className="text-sm text-muted-foreground">
                      Confidence: {(result.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-wrap">{result.answer}</p>
              </CardContent>
            </Card>

            {result.recommendations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">
                    Recommendations ({result.recommendations.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {result.recommendations.map((rec, i) => (
                    <div key={i} className="border-l-2 border-primary/30 pl-3 py-2 space-y-1">
                      <p className="text-sm">{rec.text}</p>
                      <div className="flex flex-wrap gap-2">
                        <span
                          className={cn(
                            "text-xs px-1.5 py-0.5 rounded font-medium",
                            strengthColor[rec.strength]
                          )}
                        >
                          {rec.strength}
                        </span>
                        {rec.evidence_level && (
                          <span className="text-xs text-muted-foreground">
                            Evidence: {rec.evidence_level}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Source: {rec.guideline}
                        {rec.section && ` — ${rec.section}`}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {!hasAsked && !isLoading && (
          <p className="text-center text-muted-foreground py-8">
            Ask a clinical question to get evidence-backed recommendations from clinical guidelines
          </p>
        )}
      </div>
    </ErrorBoundary>
  );
}
