"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

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

const importanceColor = (score: number) => {
  if (score >= 0.7) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100";
  if (score >= 0.4) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100";
  return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100";
};

const evidenceColors: Record<string, string> = {
  A: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  B: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
  C: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
  D: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
};

export function DigestCard({ item }: { item: DigestItem }) {
  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-2">
        <CardTitle className="text-base leading-snug">{item.title}</CardTitle>
        {item.authors.length > 0 && (
          <p className="text-xs text-muted-foreground truncate">
            {item.authors.slice(0, 5).join(", ")}
            {item.authors.length > 5 && ` et al.`}
          </p>
        )}
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {item.journal && (
            <span className="text-muted-foreground italic">{item.journal}</span>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {item.evidence_level && (
            <span className={cn("text-xs px-1.5 py-0.5 rounded font-medium", evidenceColors[item.evidence_level] || "")}>
              Evidence {item.evidence_level}
            </span>
          )}
          {item.study_design && (
            <Badge variant="secondary" className="text-xs">
              {item.study_design.replace("_", " ")}
            </Badge>
          )}
          <span className={cn("text-xs px-1.5 py-0.5 rounded", importanceColor(item.clinical_importance))}>
            {(item.clinical_importance * 100).toFixed(0)}% importance
          </span>
        </div>

        {item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {item.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-[10px]">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {item.summary_bullets.length > 0 && (
          <ul className="text-xs text-muted-foreground space-y-0.5 list-disc pl-4">
            {item.summary_bullets.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
