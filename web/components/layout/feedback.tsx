"use client";

import { useEffect, useState, useCallback } from "react";
import { cn } from "@/lib/utils";

const GH_ISSUES = "https://github.com/anomalyco/lornewspaper/issues/new";

interface DigestRating {
  date: string;
  rating: "up" | "down";
}

function getToday(): string {
  return new Date().toISOString().slice(0, 10);
}

export function Feedback() {
  const [open, setOpen] = useState(false);
  const [digestRating, setDigestRating] = useState<DigestRating | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("lornews-digest-rating");
    if (stored) {
      try {
        const parsed: DigestRating = JSON.parse(stored);
        if (parsed.date === getToday()) setDigestRating(parsed);
      } catch {
        // ignore
      }
    }
  }, []);

  const rateDigest = useCallback((rating: "up" | "down") => {
    const entry: DigestRating = { date: getToday(), rating };
    localStorage.setItem("lornews-digest-rating", JSON.stringify(entry));
    setDigestRating(entry);
    setOpen(false);
  }, []);

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {open && (
        <div className="absolute bottom-14 right-0 mb-2 w-64 rounded-lg border bg-card text-card-foreground shadow-lg p-3 space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Feedback</p>

          <a
            href={`${GH_ISSUES}?template=bug_report.md&labels=bug`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 w-full rounded-md px-2 py-1.5 text-sm hover:bg-accent transition-colors"
          >
            <span>🐞</span>
            <span>Report issue</span>
          </a>

          <a
            href={`${GH_ISSUES}?template=feature_request.md&labels=enhancement`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 w-full rounded-md px-2 py-1.5 text-sm hover:bg-accent transition-colors"
          >
            <span>💡</span>
            <span>Suggest improvement</span>
          </a>

          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground mb-1.5">
              Today&apos;s digest helpful?
            </p>
            <div className="flex gap-2">
              {digestRating?.rating === "up" ? (
                <span className="text-xs text-green-600 font-medium px-2 py-1 rounded bg-green-50 dark:bg-green-950">
                  👍 Thanks!
                </span>
              ) : digestRating?.rating === "down" ? (
                <span className="text-xs text-red-600 font-medium px-2 py-1 rounded bg-red-50 dark:bg-red-950">
                  👎 Noted
                </span>
              ) : (
                <>
                  <button
                    onClick={() => rateDigest("up")}
                    className={cn(
                      "flex-1 rounded-md border px-2 py-1 text-sm hover:bg-accent transition-colors"
                    )}
                  >
                    👍 Yes
                  </button>
                  <button
                    onClick={() => rateDigest("down")}
                    className={cn(
                      "flex-1 rounded-md border px-2 py-1 text-sm hover:bg-accent transition-colors"
                    )}
                  >
                    👎 No
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen(!open)}
        className={cn(
          "h-10 w-10 rounded-full border bg-card text-card-foreground shadow-lg flex items-center justify-center text-lg transition-colors hover:bg-accent",
          open && "bg-accent"
        )}
        aria-label="Feedback"
      >
        💬
      </button>
    </div>
  );
}