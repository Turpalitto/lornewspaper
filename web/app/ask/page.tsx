"use client";

import { useState } from "react";
import { useAsk } from "@/lib/queries";
import { AskForm } from "@/components/ask/ask-form";
import { AnswerDisplay } from "@/components/ask/answer-display";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { RetryUi } from "@/components/shared/retry-ui";
import { LoadingState } from "@/components/shared/loading-state";

export default function AskPage() {
  const ask = useAsk();
  const [hasAsked, setHasAsked] = useState(false);

  function handleAsk(question: string) {
    ask.mutate({
      question,
      llm_provider: null,
      temperature: null,
      max_tokens: null,
    });
    setHasAsked(true);
  }

  return (
    <ErrorBoundary>
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">Ask a Question</h1>
          <p className="text-muted-foreground text-sm">
            Query indexed documents using AI-powered search
          </p>
        </div>

        <AskForm onAsk={handleAsk} isLoading={ask.isPending} />

        {ask.isPending && <LoadingState count={2} />}

        {ask.isError && (
          <RetryUi
            message={ask.error?.message || "Failed to get answer"}
            onRetry={() => ask.mutate(ask.variables!)}
          />
        )}

        {ask.isSuccess && <AnswerDisplay data={ask.data} />}

        {!hasAsked && !ask.isPending && (
          <p className="text-center text-muted-foreground py-12">
            Ask a research question to get AI-powered answers from your document
            corpus
          </p>
        )}
      </div>
    </ErrorBoundary>
  );
}
