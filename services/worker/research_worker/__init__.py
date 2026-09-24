"""Product B background worker.

Runs long AI/research/indexing tasks outside the request cycle. Tasks receive a
job ID only; durable job state lives in PostgreSQL (research_api.platform.jobs).
"""
