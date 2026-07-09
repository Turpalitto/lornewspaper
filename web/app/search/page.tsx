"use client";

import { useState } from "react";
import { useSearch } from "@/lib/queries";
import { SearchForm } from "@/components/search/search-form";
import { SearchResults } from "@/components/search/search-results";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { RetryUi } from "@/components/shared/retry-ui";

export default function SearchPage() {
  const search = useSearch();
  const [hasSearched, setHasSearched] = useState(false);

  function handleSearch(query: string, maxResults: number) {
    search.mutate({ query, max_results: maxResults });
    setHasSearched(true);
  }

  return (
    <ErrorBoundary>
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">Search Literature</h1>
          <p className="text-muted-foreground text-sm">
            Search across academic literature databases
          </p>
        </div>

        <SearchForm onSearch={handleSearch} isLoading={search.isPending} />

        {search.isPending && <LoadingState count={3} />}

        {search.isError && (
          <RetryUi
            message={search.error?.message || "Search failed"}
            onRetry={() => search.mutate(search.variables)}
          />
        )}

        {search.isSuccess && <SearchResults data={search.data} />}

        {!hasSearched && !search.isPending && (
          <p className="text-center text-muted-foreground py-12">
            Enter a query to search academic literature
          </p>
        )}
      </div>
    </ErrorBoundary>
  );
}
