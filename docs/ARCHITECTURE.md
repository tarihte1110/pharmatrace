# Architecture

Farmaiz is organized as a React frontend, a FastAPI backend, and separate
document-ingestion pipelines. The intended request flow is:

1. The frontend sends a question to the backend.
2. The backend applies safety checks and retrieves relevant indexed sources.
3. The response includes source citations for user verification.

The implementation details and deployment topology are to be documented as the
system is built.
