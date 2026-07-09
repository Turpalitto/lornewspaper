"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TopStorySection } from "./top-story";
import { ClinicalTakeawaySection } from "./clinical-takeaway";
import { ControversyCard } from "./controversy-card";
import { ResearchTimeline } from "./research-timeline";

type EditorialPaper = {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  doi: string;
  evidence_level: string;
  study_design: string;
  clinical_importance: number;
  topics: string[];
  editorial_commentary: string;
  is_top_story: boolean;
  is_breaking: boolean;
};

type TopStory = {
  headline: string;
  why_it_matters: string;
  clinical_impact: string;
  key_finding: string;
  specialist_comment: string;
  paper: EditorialPaper | null;
};

type Controversy = {
  title: string;
  topic: string;
  position_a: string;
  position_b: string;
  resolution: string;
  clinical_guidance: string;
};

type Trend = {
  name: string;
  description: string;
  paper_count: number;
  momentum: string;
};

type Takeaway = {
  headline: string;
  body: string;
  action_items: string[];
};

type EditorialDigest = {
  id: string;
  period: string;
  title: string;
  subtitle: string;
  executive_summary: string[];
  top_story: TopStory;
  breaking_findings: EditorialPaper[];
  practice_impact: string[];
  controversies: Controversy[];
  research_trends: Trend[];
  papers: EditorialPaper[];
  total_papers_reviewed: number;
  reading_time_minutes: number;
};

export function EditorialDigestView({ digest }: { digest: EditorialDigest }) {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-2 pb-4 border-b">
        <h1 className="text-3xl font-bold">{digest.title}</h1>
        {digest.subtitle && (
          <p className="text-sm text-muted-foreground">{digest.subtitle}</p>
        )}
        <div className="flex items-center justify-center gap-3 text-xs text-muted-foreground">
          <span>{digest.total_papers_reviewed} papers reviewed</span>
          <span>·</span>
          <span>{digest.reading_time_minutes} min read</span>
        </div>
      </div>

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {digest.executive_summary.map((item, i) => (
              <li key={i} className="text-sm flex items-start gap-2">
                <span className="text-primary font-bold mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Top Story */}
      {digest.top_story && digest.top_story.headline && (
        <TopStorySection story={digest.top_story} />
      )}

      {/* Practice Impact */}
      {digest.practice_impact.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="text-lg">🔄</span>
              <CardTitle className="text-lg">Practice Impact</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {digest.practice_impact.map((item, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Clinical Takeaway */}
      {digest.top_story && digest.top_story.specialist_comment && (
        <ClinicalTakeawaySection
          takeaway={{
            headline: "Key clinical insight",
            body: digest.top_story.specialist_comment,
            action_items: digest.practice_impact,
          }}
        />
      )}

      {/* Controversies */}
      {digest.controversies.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold">⚡ Research Controversies</h2>
          {digest.controversies.map((c, i) => (
            <ControversyCard key={i} controversy={c} />
          ))}
        </section>
      )}

      {/* Research Trends */}
      {digest.research_trends.length > 0 && (
        <ResearchTimeline trends={digest.research_trends} />
      )}

      {/* All Papers */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            All Papers ({digest.total_papers_reviewed})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {digest.papers.map((paper) => (
              <div key={paper.id} className="flex items-start gap-2 text-sm">
                <span className="mt-1 shrink-0">
                  {paper.is_top_story ? "⭐" : paper.is_breaking ? "🔴" : "📄"}
                </span>
                <div>
                  <p className="font-medium">{paper.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {paper.authors.slice(0, 3).join(", ")} — {paper.journal}
                  </p>
                  <div className="flex gap-1 mt-1">
                    {paper.evidence_level && (
                      <Badge variant="secondary" className="text-[10px]">
                        Evidence {paper.evidence_level}
                      </Badge>
                    )}
                    {paper.study_design && (
                      <Badge variant="outline" className="text-[10px]">
                        {paper.study_design.replace("_", " ")}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
