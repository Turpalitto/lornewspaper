"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";
import { RetryUi } from "@/components/shared/retry-ui";
import { cn } from "@/lib/utils";

type Recommendation = {
  id: string;
  text_ru: string;
  strength: string;
  evidence_level: string;
  population: string;
  contraindications: string[];
  pregnancy: string;
};

type GuidelineSection = {
  id: string;
  heading: string;
  level: number;
  content: string;
  recommendations: Recommendation[];
};

type Guideline = {
  id: string;
  title_ru: string;
  source: string;
  version: string;
  language: string;
  sections: GuidelineSection[];
  recommendations: Recommendation[];
  icd10_codes: string[];
};

const strengthColor: Record<string, string> = {
  strong: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  conditional: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
  not_recommended: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
};

export default function GuidelineDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [guideline, setGuideline] = useState<Guideline | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/v1/clinical/guidelines/${id}`);
        if (!res.ok) throw new Error(`Failed to load guideline: ${res.statusText}`);
        setGuideline(await res.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [id]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <LoadingState count={4} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <RetryUi message={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  if (!guideline) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Guideline not found</p>
      </div>
    );
  }

  const recCount = guideline.recommendations.length;
  const sectionRecs = guideline.sections.filter((s) => s.recommendations.length > 0);

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        <div>
          <Link
            href="/guidelines"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; Back to guidelines
          </Link>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">
              {guideline.title_ru || "Untitled Guideline"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Badge>{guideline.source}</Badge>
              {guideline.version && <Badge variant="secondary">v{guideline.version}</Badge>}
              <Badge variant="secondary">{guideline.language}</Badge>
            </div>
            <div className="text-sm text-muted-foreground">
              <p>Recommendations: {recCount}</p>
            </div>
            {guideline.icd10_codes.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {guideline.icd10_codes.map((code) => (
                  <Badge key={code} variant="outline">{code}</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {sectionRecs.map((section) => (
          <Card key={section.id}>
            <CardHeader>
              <CardTitle className="text-lg">{section.heading || "General"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {section.content}
              </p>
              {section.recommendations.map((rec) => (
                <div key={rec.id} className="border rounded-lg p-4 space-y-2 bg-accent/30">
                  <p className="text-sm font-medium">{rec.text_ru}</p>
                  <div className="flex flex-wrap gap-2">
                    <span
                      className={cn(
                        "text-xs px-2 py-0.5 rounded font-medium",
                        strengthColor[rec.strength]
                      )}
                    >
                      {rec.strength.replace("_", " ")}
                    </span>
                    {rec.evidence_level && (
                      <span className="text-xs text-muted-foreground">
                        Evidence: {rec.evidence_level}
                      </span>
                    )}
                    {rec.population && (
                      <span className="text-xs text-muted-foreground">
                        Population: {rec.population}
                      </span>
                    )}
                  </div>
                  {rec.contraindications.length > 0 && (
                    <div className="text-xs text-destructive">
                      Contraindications: {rec.contraindications.join("; ")}
                    </div>
                  )}
                  {rec.pregnancy && rec.pregnancy !== "unknown" && (
                    <div className="text-xs text-amber-600">
                      Pregnancy: {rec.pregnancy}
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </ErrorBoundary>
  );
}
