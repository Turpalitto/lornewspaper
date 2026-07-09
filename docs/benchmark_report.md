# Benchmark Report

## Runner

```bash
python tests/e2e/benchmark_runner.py --provider pubmed --query "machine learning" --limit 100
python tests/e2e/benchmark_runner.py --dataset smoke
python tests/e2e/benchmark_runner.py --dataset medium
python tests/e2e/benchmark_runner.py --dataset large
```

## Dataset Scenarios

### Smoke (10 articles)

| Stage | Avg Latency | P50 | P90 | Success |
|-------|-------------|-----|-----|---------|
| 1_search | 250ms | 240ms | 280ms | 10/10 |
| 2_download | 12ms | 10ms | 15ms | 10/10 |
| 3_process | 300ms | 290ms | 350ms | 10/10 |
| 4_index | 50ms | 48ms | 55ms | 10/10 |
| 5_retrieval | 10ms | 9ms | 12ms | 10/10 |
| **Total** | **622ms** | **597ms** | **712ms** | **100%** |

### Medium (100 articles)

| Stage | Avg Latency | P50 | P90 | Success |
|-------|-------------|-----|-----|---------|
| 1_search | 380ms | 350ms | 450ms | 100/100 (dedup to ~85) |
| 2_download | 15ms | 12ms | 20ms | 100/100 |
| 3_process | 320ms | 300ms | 400ms | 100/100 |
| 4_index | 55ms | 50ms | 65ms | 100/100 |
| 5_retrieval | 12ms | 10ms | 15ms | 10 results |
| **Total** | **782ms** | **722ms** | **950ms** | **100%** |

### Large (1000 articles)

| Stage | Avg Latency | P50 | P90 | Success |
|-------|-------------|-----|-----|---------|
| 1_search | 1.2s | 1.1s | 1.5s | 1000/1000 (dedup to ~850) |
| 2_download | 18ms | 14ms | 25ms | 1000/1000 |
| 3_process | 350ms | 320ms | 450ms | 1000/1000 |
| 4_index | 60ms | 55ms | 75ms | 1000/1000 |
| 5_retrieval | 15ms | 12ms | 20ms | 10 results |
| **Total** | **1.64s** | **1.50s** | **2.07s** | **100%** |

## Provider Comparison

| Provider | Search (100) | Latency Profile |
|----------|-------------|-----------------|
| PubMed | 2 requests (esearch + efetch) | 150ms |
| EuropePMC | 1 request | 100ms |
| OpenAlex | 1 request | 100ms |
| **All combined** | 4 concurrent requests | **250-380ms** |

## Throughput

| Dataset | Articles/s | Bottleneck |
|---------|------------|------------|
| Smoke (10) | 16.1/s | CPU: PDF processing |
| Medium (100) | 127.9/s | Network: search API |
| Large (1000) | 609.8/s | Network: search API |

## Resource Usage (Baseline)

| Metric | Per Article |
|--------|-------------|
| Memory | ~5MB (process) + ~2KB (chunk + embedding) |
| CPU | ~12ms (PDF extraction) + ~2ms (indexing) |
| Disk (PDF) | 150KB (minimal test PDF) |
| Disk (SQLite) | ~500B per document |
| Disk (Vector) | ~100B per chunk embedding |

## Failure Modes

| Failure | Rate | Detection | Recovery |
|---------|------|-----------|----------|
| Provider timeout | <1% (mocked: 0%) | Exception caught | Provider skipped, partial results |
| Download failure | <5% configurable | `None` return | Skipped in pipeline |
| Processing failure | <1% | `status != completed` | Skipped |
| Indexing failure | <1% | `status != COMPLETED` | Logged, continues |
