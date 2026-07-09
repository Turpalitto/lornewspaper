"use client";

import Link from "next/link";
import type { components } from "@/lib/api-types";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";

type DocumentRecord = components["schemas"]["DocumentRecord"];

type DocumentCardProps = {
  document: DocumentRecord;
};

export function DocumentCard({ document }: DocumentCardProps) {
  const meta = document.metadata;

  return (
    <Link
      href={`/documents/${document.document_id}`}
      className="block border rounded-lg p-4 hover:border-primary hover:shadow-sm transition-all space-y-2"
    >
      <h3 className="font-medium leading-snug line-clamp-2">
        {meta?.title || "Untitled"}
      </h3>

      {meta?.authors && meta.authors.length > 0 && (
        <p className="text-sm text-muted-foreground truncate">
          {meta.authors.join(", ")}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 text-xs">
        {meta?.year && <Badge variant="secondary">{meta.year}</Badge>}
        <span className="text-muted-foreground">
          {document.chunk_count} chunks
        </span>
        {document.created_at && (
          <span className="text-muted-foreground">
            {formatDate(document.created_at)}
          </span>
        )}
      </div>
    </Link>
  );
}
