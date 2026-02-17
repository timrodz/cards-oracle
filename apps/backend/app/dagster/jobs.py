from dagster import Field, Noneable, job, op

from app.data_pipeline.create_embeddings import Embeddings


@op(
    config_schema={
        "source_collection": Field(str),
        "target_collection": Field(str),
        "chunk_mappings": Field(Noneable(str), is_required=False, default_value=None),
        "limit": Field(Noneable(int), is_required=False, default_value=None),
        "normalize": Field(bool, default_value=True),
    }
)
def create_embeddings_op(context) -> None:
    config = context.op_config

    embeddings = Embeddings()
    embeddings.run_pipeline(
        source_collection=config["source_collection"],
        target_collection=config["target_collection"],
        chunk_mappings=config.get("chunk_mappings"),
        limit=config.get("limit"),
        normalize=config["normalize"],
    )


@job(name="create_embeddings_job")
def create_embeddings_job():
    create_embeddings_op()
