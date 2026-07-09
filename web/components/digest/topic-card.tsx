"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Topic = {
  id: string;
  display_name: string;
  icon: string;
  paper_count: number;
  summary: string;
};

export function TopicCard({ topic }: { topic: Topic }) {
  return (
    <Link href={`/digest/topic/${topic.id}`}>
      <Card className="hover:border-primary/50 transition-colors h-full">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{topic.icon || "📄"}</span>
              <CardTitle className="text-lg">{topic.display_name}</CardTitle>
            </div>
            <Badge>{topic.paper_count} papers</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {topic.summary || `Recent developments in ${topic.display_name}.`}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}
