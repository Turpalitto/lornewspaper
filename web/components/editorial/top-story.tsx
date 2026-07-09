"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type TopStoryProps = {
  headline: string;
  why_it_matters: string;
  clinical_impact: string;
  key_finding: string;
  specialist_comment: string;
  paper?: {
    title: string;
    journal: string;
    authors: string[];
    evidence_level: string;
  } | null;
};

export function TopStorySection({ story }: { story: TopStoryProps }) {
  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardHeader>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-lg">⭐</span>
          <span className="text-xs font-semibold text-primary uppercase tracking-wider">
            {"Editor\u2019s Pick"}
          </span>
        </div>
        <CardTitle className="text-xl leading-snug">{story.headline}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-1">Why It Matters</h3>
          <p className="text-sm">{story.why_it_matters}</p>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-1">Clinical Impact</h3>
          <p className="text-sm">{story.clinical_impact}</p>
        </div>

        {story.key_finding && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-1">Key Finding</h3>
            <p className="text-sm">{story.key_finding}</p>
          </div>
        )}

        {story.specialist_comment && (
          <div className="border-l-2 border-primary/30 pl-3 italic">
            <p className="text-sm text-muted-foreground">{story.specialist_comment}</p>
          </div>
        )}

        {story.paper && (
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground pt-2 border-t">
            <span>{story.paper.journal}</span>
            <span>{story.paper.authors.slice(0, 3).join(", ")}</span>
            {story.paper.evidence_level && (
              <Badge variant="secondary">Evidence {story.paper.evidence_level}</Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
