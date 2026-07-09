"use client";

import { useHealth, useReadiness } from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";
import { RetryUi } from "@/components/shared/retry-ui";
import { formatMs } from "@/lib/utils";

export default function SettingsPage() {
  const health = useHealth();
  const readiness = useReadiness();

  return (
    <ErrorBoundary>
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">Settings</h1>
          <p className="text-muted-foreground text-sm">
            System status and configuration
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {health.isLoading && <LoadingState count={1} />}
            {health.isError && (
              <RetryUi
                message={health.error?.message || "Health check failed"}
                onRetry={() => health.refetch()}
              />
            )}
            {health.isSuccess && (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Status:</span>
                  <Badge
                    variant={
                      health.data.status === "ok" ? "default" : "destructive"
                    }
                  >
                    {health.data.status}
                  </Badge>
                </div>
                <p>
                  <span className="text-muted-foreground">Version:</span>{" "}
                  {health.data.version}
                </p>
                <p>
                  <span className="text-muted-foreground">Uptime:</span>{" "}
                  {formatMs(health.data.uptime_seconds * 1000)}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Service Readiness</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {readiness.isLoading && <LoadingState count={1} />}
            {readiness.isError && (
              <RetryUi
                message={
                  readiness.error?.message || "Readiness check failed"
                }
                onRetry={() => readiness.refetch()}
              />
            )}
            {readiness.isSuccess && (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Status:</span>
                  <Badge
                    variant={
                      readiness.data.status === "ok"
                        ? "default"
                        : "destructive"
                    }
                  >
                    {readiness.data.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Agent:</span>
                  <Badge
                    variant={
                      readiness.data.agent_ready ? "default" : "secondary"
                    }
                  >
                    {readiness.data.agent_ready ? "Ready" : "Not Ready"}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">
                    Knowledge Base:
                  </span>
                  <Badge
                    variant={
                      readiness.data.knowledge_base_ready
                        ? "default"
                        : "secondary"
                    }
                  >
                    {readiness.data.knowledge_base_ready
                      ? "Ready"
                      : "Not Ready"}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Cache:</span>
                  <Badge
                    variant={
                      readiness.data.cache_ready ? "default" : "secondary"
                    }
                  >
                    {readiness.data.cache_ready ? "Ready" : "Not Ready"}
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ErrorBoundary>
  );
}
