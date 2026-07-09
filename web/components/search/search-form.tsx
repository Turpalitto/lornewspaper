"use client";

import { useState, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";

type SearchFormProps = {
  onSearch: (query: string, maxResults: number) => void;
  isLoading: boolean;
};

export function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(10);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim(), maxResults);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="Search academic literature..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1"
          aria-label="Search query"
        />
        <Button type="submit" disabled={isLoading || !query.trim()}>
          {isLoading ? "Searching..." : "Search"}
        </Button>
      </div>
      <div className="flex items-center gap-2">
        <label htmlFor="max-results" className="text-sm text-muted-foreground">
          Max results:
        </label>
        <Select
          id="max-results"
          value={String(maxResults)}
          onChange={(e) => setMaxResults(Number(e.target.value))}
          options={[
            { value: "5", label: "5" },
            { value: "10", label: "10" },
            { value: "20", label: "20" },
            { value: "50", label: "50" },
          ]}
          className="w-20"
        />
      </div>
    </form>
  );
}
