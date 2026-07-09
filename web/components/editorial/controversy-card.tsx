"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ControversyProps = {
  title: string;
  topic: string;
  position_a: string;
  position_b: string;
  resolution: string;
  clinical_guidance: string;
};

export function ControversyCard({ controversy }: { controversy: ControversyProps }) {
  return (
    <Card className="border-red-200 dark:border-red-800">
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="text-lg">⚡</span>
          <CardTitle className="text-base">{controversy.title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="border-l-2 border-blue-400 pl-3">
            <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">Position A</p>
            <p className="text-sm">{controversy.position_a}</p>
          </div>
          <div className="border-l-2 border-red-400 pl-3">
            <p className="text-xs font-semibold text-red-600 dark:text-red-400 mb-1">Position B</p>
            <p className="text-sm">{controversy.position_b}</p>
          </div>
        </div>

        <div className="bg-muted/50 rounded p-3">
          <p className="text-xs font-semibold text-muted-foreground mb-1">Resolution</p>
          <p className="text-sm text-muted-foreground">{controversy.resolution}</p>
        </div>

        <div className="bg-amber-50 dark:bg-amber-900/20 rounded p-3">
          <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 mb-1">Clinical Guidance</p>
          <p className="text-sm text-amber-800 dark:text-amber-300">{controversy.clinical_guidance}</p>
        </div>
      </CardContent>
    </Card>
  );
}
