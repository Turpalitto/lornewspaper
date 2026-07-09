"use client";

import { useState } from "react";
import Link from "next/link";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { EmptyState } from "@/components/shared/empty-state";

export default function SavedPapersPage() {
  const [saved] = useState<string[]>(() => {
    if (typeof window !== "undefined") {
      return JSON.parse(localStorage.getItem("digest_bookmarks") || "[]");
    }
    return [];
  });

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <Link href="/digest" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            &larr; Back to digest
          </Link>
        </div>

        <h1 className="text-2xl font-bold mb-2">Saved Papers</h1>
        <p className="text-sm text-muted-foreground mb-6">
          Papers you have bookmarked for later reading.
        </p>

        {saved.length === 0 ? (
          <EmptyState
            title="No saved papers yet"
            description="Click the bookmark icon on any paper to save it for later reading."
            action={
              <Link href="/digest">
                <span className="text-primary hover:underline text-sm">{"Browse today\u2019s digest"}</span>
              </Link>
            }
          />
        ) : (
          <p className="text-sm text-muted-foreground">
            {saved.length} saved paper{saved.length !== 1 ? "s" : ""}
          </p>
        )}
      </div>
    </ErrorBoundary>
  );
}
