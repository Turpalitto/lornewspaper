import createClient from "openapi-fetch";
import type { paths } from "./api-types";

export const client = createClient<paths>({
  baseUrl: typeof window !== "undefined" ? "" : "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export type ErrorResponse = {
  code: string;
  message: string;
  details: Record<string, unknown>;
  request_id: string;
  timestamp: string;
};

export function isErrorResponse(err: unknown): err is ErrorResponse {
  return (
    typeof err === "object" &&
    err !== null &&
    "code" in err &&
    "message" in err
  );
}
