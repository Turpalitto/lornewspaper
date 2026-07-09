"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import {
  useDocument,
  useDocumentChunks,
  useDocumentSummary,
  useDocumentSimilar,
} from "@/lib/queries";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { RetryUi } from "@/components/shared/retry-ui";
import { formatDate } from "@/lib/utils";

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const doc = useDocument(id);
  const chunks = useDocumentChunks(id);
  const summary = useDocumentSummary(id);
  const similar = useDocumentSimilar(id);

  if (doc.isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <LoadingState count={4} />
      </div>
    );
  }

  if (doc.isError) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <RetryUi
          message={doc.error?.message || "Failed to load document"}
          onRetry={() => doc.refetch()}
        />
      </div>
    );
  }

  const metadata = doc.data?.metadata;

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        <div>
          <Link
            href="/documents"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; Back to documents
          </Link>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{metadata?.title || "Untitled"}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {metadata?.authors && metadata.authors.length > 0 && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Authors
                </p>
                <p className="text-sm">{metadata.authors.join(", ")}</p>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              {metadata?.year && <Badge>{metadata.year}</Badge>}
              {metadata?.source && (
                <Badge variant="secondary">{metadata.source}</Badge>
              )}
              {metadata?.doi && (
                <span className="text-xs text-muted-foreground font-mono">
                  DOI: {metadata.doi}
                </span>
              )}
            </div>

            <div className="text-xs text-muted-foreground">
              <p>Document ID: {doc.data?.document_id}</p>
              {doc.data?.created_at && (
                <p>Created: {formatDate(doc.data.created_at)}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {summary.isLoading && (
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <LoadingState count={1} />
            </CardContent>
          </Card>
        )}
        {summary.isError && (
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Failed to load summary
              </p>
            </CardContent>
          </Card>
        )}
        {summary.isSuccess && (
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap">
                {summary.data.summary}
              </p>
              <div className="flex gap-2 mt-3 text-xs text-muted-foreground">
                <span>
                  {summary.data.llm_provider} / {summary.data.llm_model}
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {chunks.isLoading && (
          <Card>
            <CardHeader>
              <CardTitle>Content Chunks</CardTitle>
            </CardHeader>
            <CardContent>
              <LoadingState count={3} />
            </CardContent>
          </Card>
        )}
        {chunks.isSuccess && chunks.data.items && (
          <Card>
            <CardHeader>
              <CardTitle>
                Content Chunks ({chunks.data.items.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {chunks.data.items.map((chunk) => (
                <div
                  key={chunk.chunk_id}
                  className="text-sm border-l-2 pl-3 py-1"
                >
                  {chunk.heading && (
                    <p className="font-medium text-xs text-muted-foreground mb-1">
                      {chunk.heading}
                    </p>
                  )}
                  <p>{chunk.text}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {similar.isSuccess && (
          <Card>
            <CardHeader>
              <CardTitle>Similar Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm whitespace-pre-wrap">
                {similar.data.analysis}
              </p>
              {similar.data.related_documents &&
                similar.data.related_documents.length > 0 && (
                  <ul className="space-y-1">
                    {similar.data.related_documents.map((docId, i) => (
                      <li key={i}>
                        <Link
                          href={`/documents/${docId}`}
                          className="text-sm text-primary hover:underline"
                        >
                          {docId}
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
            </CardContent>
          </Card>
        )}
      </div>
    </ErrorBoundary>
  );
}
