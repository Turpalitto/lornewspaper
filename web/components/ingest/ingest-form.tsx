"use client";

import { useState, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";

type IngestFormProps = {
  onIngest: (query: string, maxResults: number) => void;
  onDownload: (query: string, maxResults: number) => void;
  isIngesting: boolean;
  isDownloading: boolean;
};

export function IngestForm({
  onIngest,
  onDownload,
  isIngesting,
  isDownloading,
}: IngestFormProps) {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(5);

  function handleIngest(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    onIngest(query.trim(), maxResults);
  }

  function handleDownload(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    onDownload(query.trim(), maxResults);
  }

  const isBusy = isIngesting || isDownloading;

  return (
    <form className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="Search query for articles to ingest..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1"
          aria-label="Ingest query"
        />
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        <label
          htmlFor="ingest-max-results"
          className="text-sm text-muted-foreground"
        >
          Max results:
        </label>
        <Select
          id="ingest-max-results"
          value={String(maxResults)}
          onChange={(e) => setMaxResults(Number(e.target.value))}
          options={[
            { value: "3", label: "3" },
            { value: "5", label: "5" },
            { value: "10", label: "10" },
            { value: "20", label: "20" },
          ]}
          className="w-20"
        />
        <div className="flex gap-2 ml-auto">
          <Button
            type="button"
            variant="outline"
            disabled={isBusy || !query.trim()}
            onClick={handleDownload}
          >
            {isDownloading ? "Downloading..." : "Download Only"}
          </Button>
          <Button
            type="submit"
            disabled={isBusy || !query.trim()}
            onClick={handleIngest}
          >
            {isIngesting ? "Ingesting..." : "Search & Ingest"}
          </Button>
        </div>
      </div>
    </form>
  );
}
