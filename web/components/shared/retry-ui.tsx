import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type RetryUiProps = {
  message?: string;
  onRetry?: () => void;
};

export function RetryUi({
  message = "Failed to load data",
  onRetry,
}: RetryUiProps) {
  return (
    <Card className="mx-auto max-w-md">
      <CardContent className="pt-6 text-center space-y-4">
        <p className="text-sm text-muted-foreground">{message}</p>
        {onRetry && (
          <Button variant="outline" onClick={onRetry}>
            Try again
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
