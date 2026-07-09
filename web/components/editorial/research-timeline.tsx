"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type TrendProps = {
  name: string;
  description: string;
  paper_count: number;
  momentum: string;
};

const momentumColors: Record<string, string> = {
  emerging: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
  growing: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
  established: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100",
  declining: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100",
};

export function ResearchTimeline({ trends }: { trends: TrendProps[] }) {
  if (trends.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="text-lg">📊</span>
          <CardTitle className="text-lg">Research Trends</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {trends.slice(0, 5).map((trend) => (
            <div key={trend.name} className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium">{trend.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${momentumColors[trend.momentum] || ""}`}>
                    {trend.momentum}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {trend.paper_count} papers
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {trend.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
