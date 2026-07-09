"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from "@tanstack/react-query";
import { client } from "./api-client";
import type { paths, components } from "./api-types";
import type { ErrorResponse } from "./api-client";

type SearchParams = paths["/api/v1/search"]["post"]["requestBody"]["content"]["application/json"];
type SearchResponse = paths["/api/v1/search"]["post"]["responses"]["200"]["content"]["application/json"];

type IngestParams = paths["/api/v1/ingest"]["post"]["requestBody"]["content"]["application/json"];
type IngestResponse = paths["/api/v1/ingest"]["post"]["responses"]["200"]["content"]["application/json"];

type AskParams = paths["/api/v1/ask"]["post"]["requestBody"]["content"]["application/json"];
type AskResponse = paths["/api/v1/ask"]["post"]["responses"]["200"]["content"]["application/json"];

type DocListParams = paths["/api/v1/documents"]["get"]["parameters"]["query"];
type DocListResponse = paths["/api/v1/documents"]["get"]["responses"]["200"]["content"]["application/json"];

type DocDetailResponse = paths["/api/v1/documents/{document_id}"]["get"]["responses"]["200"]["content"]["application/json"];

type ChunksResponse = paths["/api/v1/documents/{document_id}/chunks"]["get"]["responses"]["200"]["content"]["application/json"];

type SummaryResponse = paths["/api/v1/documents/{document_id}/summary"]["get"]["responses"]["200"]["content"]["application/json"];

type SimilarResponse = paths["/api/v1/documents/{document_id}/similar"]["get"]["responses"]["200"]["content"]["application/json"];

type HealthResponse = paths["/api/v1/health"]["get"]["responses"]["200"]["content"]["application/json"];

type ReadinessResponse = paths["/api/v1/readiness"]["get"]["responses"]["200"]["content"]["application/json"];

// ----- Health -----

export function useHealth(options?: UseQueryOptions<HealthResponse>) {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await client.GET("/api/v1/health");
      if (error) throw (error as ErrorResponse) || new Error("Health check failed");
      return data!;
    },
    refetchInterval: 30_000,
    ...options,
  });
}

export function useReadiness(options?: UseQueryOptions<ReadinessResponse>) {
  return useQuery<ReadinessResponse>({
    queryKey: ["readiness"],
    queryFn: async () => {
      const { data, error } = await client.GET("/api/v1/readiness");
      if (error) throw (error as ErrorResponse) || new Error("Readiness check failed");
      return data!;
    },
    refetchInterval: 15_000,
    ...options,
  });
}

// ----- Search -----

export function useSearch() {
  return useMutation<SearchResponse, Error, SearchParams>({
    mutationFn: async (params) => {
      const { data, error } = await client.POST("/api/v1/search", {
        body: params,
      });
      if (error) throw (error as ErrorResponse) || new Error("Search failed");
      return data!;
    },
  });
}

// ----- Ingest -----

export function useIngest() {
  const qc = useQueryClient();
  return useMutation<IngestResponse, Error, IngestParams>({
    mutationFn: async (params) => {
      const { data, error } = await client.POST("/api/v1/ingest", {
        body: params,
      });
      if (error) throw (error as ErrorResponse) || new Error("Ingest failed");
      return data!;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDownload() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (params: { query: string; max_results: number }) => {
      const { data, error } = await client.POST("/api/v1/ingest/download", {
        body: params,
      });
      if (error) throw (error as ErrorResponse) || new Error("Download failed");
      return data!;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

// ----- Ask -----

export function useAsk() {
  return useMutation<AskResponse, Error, AskParams>({
    mutationFn: async (params) => {
      const { data, error } = await client.POST("/api/v1/ask", {
        body: params,
      });
      if (error) throw (error as ErrorResponse) || new Error("Ask failed");
      return data!;
    },
  });
}

// ----- Documents -----

export function useDocuments(params: DocListParams) {
  return useQuery<DocListResponse>({
    queryKey: ["documents", params],
    queryFn: async () => {
      const { data, error } = await client.GET("/api/v1/documents", {
        params: { query: params },
      });
      if (error) throw (error as ErrorResponse) || new Error("Failed to fetch documents");
      return data!;
    },
  });
}

export function useDocument(id: string) {
  return useQuery<DocDetailResponse>({
    queryKey: ["document", id],
    queryFn: async () => {
      const { data, error } = await client.GET("/api/v1/documents/{document_id}", {
        params: { path: { document_id: id } },
      });
      if (error) throw (error as ErrorResponse) || new Error("Failed to fetch document");
      return data!;
    },
    enabled: !!id,
  });
}

export function useDocumentChunks(id: string, cursor?: string, limit = 20) {
  return useQuery<ChunksResponse>({
    queryKey: ["document-chunks", id, cursor, limit],
    queryFn: async () => {
      const { data, error } = await client.GET("/api/v1/documents/{document_id}/chunks", {
        params: { path: { document_id: id }, query: { cursor, limit } },
      });
      if (error) throw (error as ErrorResponse) || new Error("Failed to fetch chunks");
      return data!;
    },
    enabled: !!id,
  });
}

export function useDocumentSummary(id: string) {
  return useQuery<SummaryResponse>({
    queryKey: ["document-summary", id],
    queryFn: async () => {
      const { data, error } = await client.GET("/api/v1/documents/{document_id}/summary", {
        params: { path: { document_id: id } },
      });
      if (error) throw (error as ErrorResponse) || new Error("Failed to fetch summary");
      return data!;
    },
    enabled: !!id,
  });
}

export function useDocumentSimilar(id: string) {
  return useQuery<SimilarResponse>({
    queryKey: ["document-similar", id],
    queryFn: async () => {
      const { data, error } = await client.GET("/api/v1/documents/{document_id}/similar", {
        params: { path: { document_id: id } },
      });
      if (error) throw (error as ErrorResponse) || new Error("Failed to fetch similar docs");
      return data!;
    },
    enabled: !!id,
  });
}
