"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type TakeawayProps = {
  headline: string;
  body: string;
  action_items: string[];
};

export function ClinicalTakeawaySection({ takeaway }: { takeaway: TakeawayProps }) {
  return (
    <Card className="border-amber-200 dark:border-amber-800">
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="text-lg">🏥</span>
          <CardTitle className="text-lg">Today{"\u2019"}s Clinical Takeaway</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm font-medium">{takeaway.headline}</p>
        <p className="text-sm text-muted-foreground">{takeaway.body}</p>

        {takeaway.action_items.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Action Items
            </p>
            <ul className="space-y-1">
              {takeaway.action_items.map((item, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
