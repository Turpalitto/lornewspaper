"use client";

import type { components } from "@/lib/api-types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatMs } from "@/lib/utils";

type AskResponse = {
  answer: components["schemas"]["AnswerResponse"];
  chunks?: components["schemas"]["ChunkInfo"][];
  elapsed_ms: number;
};

type AnswerDisplayProps = {
  data: AskResponse;
};

export function AnswerDisplay({ data }: AnswerDisplayProps) {
  const { answer, elapsed_ms } = data;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Answer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {answer.answer}
          </div>

          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary">
              Confidence: {Math.round(answer.confidence * 100)}%
            </Badge>
            <span>{answer.llm_provider} / {answer.llm_model}</span>
            <span>{formatMs(answer.llm_elapsed_ms)} LLM</span>
            <span>{formatMs(elapsed_ms)} total</span>
          </div>
        </CardContent>
      </Card>

      {answer.sources && answer.sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {answer.sources.map((source, i) => (
                <li
                  key={i}
                  className="text-sm text-muted-foreground truncate"
                >
                  {source}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {data.chunks && data.chunks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Context Chunks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.chunks.map((chunk, i) => (
              <div key={i} className="text-sm border-l-2 pl-3 py-1">
                {chunk.heading && (
                  <p className="font-medium text-xs text-muted-foreground mb-1">
                    {chunk.heading}
                  </p>
                )}
                <p className="line-clamp-3">{chunk.text}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Score: {(chunk.score * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
