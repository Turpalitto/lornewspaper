"use client";

import type { components } from "@/lib/api-types";
import { Badge } from "@/components/ui/badge";
import { formatMs } from "@/lib/utils";

type Article = components["schemas"]["ArticleResponse"];
type SearchResponse = {
  articles?: Article[];
  total: number;
  elapsed_ms: number;
};

type SearchResultsProps = {
  data: SearchResponse;
};

export function SearchResults({ data }: SearchResultsProps) {
  const articles = data.articles ?? [];

  if (articles.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-8">
        No results found
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{data.total} results</span>
        <span>{formatMs(data.elapsed_ms)}</span>
      </div>

      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}

function ArticleCard({ article }: { article: Article }) {
  return (
    <div className="border rounded-lg p-4 space-y-2">
      <h3 className="font-medium leading-snug">{article.title}</h3>

      {article.authors && article.authors.length > 0 && (
        <p className="text-sm text-muted-foreground">
          {article.authors.join(", ")}
        </p>
      )}

      <div className="flex flex-wrap gap-2 text-xs">
        {article.year && <Badge variant="secondary">{article.year}</Badge>}
        {article.journal && (
          <span className="text-muted-foreground">{article.journal}</span>
        )}
        {article.doi && (
          <span className="text-muted-foreground font-mono text-xs">
            DOI: {article.doi}
          </span>
        )}
      </div>

      {article.abstract && (
        <p className="text-sm text-muted-foreground line-clamp-3">
          {article.abstract}
        </p>
      )}
    </div>
  );
}
