import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle className="text-center">{title}</CardTitle>
      </CardHeader>
      {description && (
        <CardContent className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">{description}</p>
          {action}
        </CardContent>
      )}
    </Card>
  );
}
