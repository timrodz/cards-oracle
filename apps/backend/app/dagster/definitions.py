from dagster import Definitions

from app.dagster.jobs import create_embeddings_job

defs = Definitions(jobs=[create_embeddings_job])

