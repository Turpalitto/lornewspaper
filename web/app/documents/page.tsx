"use client";

import { useDocuments } from "@/lib/queries";
import { DocumentList } from "@/components/documents/document-list";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { RetryUi } from "@/components/shared/retry-ui";
import { EmptyState } from "@/components/shared/empty-state";

export default function DocumentsPage() {
  const { data, isLoading, isError, error, refetch } = useDocuments({});

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">Documents</h1>
          <p className="text-muted-foreground text-sm">
            Browse indexed documents
          </p>
        </div>

        {isLoading && <LoadingState count={6} />}

        {isError && (
          <RetryUi
            message={error?.message || "Failed to load documents"}
            onRetry={() => refetch()}
          />
        )}

        {data && data.items && data.items.length > 0 && (
          <DocumentList data={data} />
        )}

        {data && (!data.items || data.items.length === 0) && (
          <EmptyState
            title="No documents"
            description="Documents will appear here once they are indexed through the ingest pipeline."
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
