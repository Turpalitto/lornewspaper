"use client";

import type { components } from "@/lib/api-types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatMs } from "@/lib/utils";

type IngestResponse = {
  documents?: components["schemas"]["IngestDocumentResponse"][];
  total: number;
  elapsed_ms: number;
};

type IngestResultsProps = {
  data: IngestResponse;
};

export function IngestResults({ data }: IngestResultsProps) {
  const docs = data.documents ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Ingest Complete — {data.total} document{data.total !== 1 ? "s" : ""}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Completed in {formatMs(data.elapsed_ms)}
        </p>

        {docs.length > 0 && (
          <div className="space-y-2">
            {docs.map((doc) => (
              <div
                key={doc.document_id}
                className="flex items-center justify-between border rounded p-3 text-sm"
              >
                <div className="space-y-1">
                  <p className="font-mono text-xs text-muted-foreground">
                    {doc.document_id}
                  </p>
                  <Badge
                    variant={
                      doc.status === "ingested" ? "default" : "secondary"
                    }
                  >
                    {doc.status}
                  </Badge>
                </div>
                <span className="text-muted-foreground text-xs">
                  {doc.chunks} chunks
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
