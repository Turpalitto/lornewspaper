"use client";

import { useIngest, useDownload } from "@/lib/queries";
import { IngestForm } from "@/components/ingest/ingest-form";
import { IngestResults } from "@/components/ingest/ingest-results";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { RetryUi } from "@/components/shared/retry-ui";

export default function IngestPage() {
  const ingest = useIngest();
  const download = useDownload();

  function handleIngest(query: string, maxResults: number) {
    ingest.mutate({ query, max_results: maxResults });
  }

  function handleDownload(query: string, maxResults: number) {
    download.mutate({ query, max_results: maxResults });
  }

  return (
    <ErrorBoundary>
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">Ingest Articles</h1>
          <p className="text-muted-foreground text-sm">
            Search, download, process, and index academic articles
          </p>
        </div>

        <IngestForm
          onIngest={handleIngest}
          onDownload={handleDownload}
          isIngesting={ingest.isPending}
          isDownloading={download.isPending}
        />

        {ingest.isError && (
          <RetryUi
            message={ingest.error?.message || "Ingest failed"}
            onRetry={() => ingest.mutate(ingest.variables!)}
          />
        )}

        {download.isError && (
          <RetryUi
            message={download.error?.message || "Download failed"}
            onRetry={() => download.mutate(download.variables!)}
          />
        )}

        {ingest.isSuccess && <IngestResults data={ingest.data} />}

        {!ingest.isSuccess && !download.isSuccess && (
          <p className="text-center text-muted-foreground py-12">
            Enter a search query to find and ingest academic articles
          </p>
        )}
      </div>
    </ErrorBoundary>
  );
}
