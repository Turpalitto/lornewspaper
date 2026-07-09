"use client";

import type { components } from "@/lib/api-types";
import { DocumentCard } from "./document-card";

type DocumentListResponse = {
  items?: components["schemas"]["DocumentRecord"][];
  has_more: boolean;
  next_cursor?: string | null;
  limit: number;
};

type DocumentListProps = {
  data: DocumentListResponse;
  onLoadMore?: () => void;
  isLoadingMore?: boolean;
};

export function DocumentList({
  data,
  onLoadMore,
  isLoadingMore,
}: DocumentListProps) {
  const items = data.items ?? [];

  if (items.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-8">
        No documents indexed yet
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        {items.length} document{items.length !== 1 ? "s" : ""}
        {data.has_more ? " (more available)" : ""}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((doc) => (
          <DocumentCard key={doc.document_id} document={doc} />
        ))}
      </div>
    </div>
  );
}
