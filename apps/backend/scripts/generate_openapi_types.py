#!/usr/bin/env python3

import argparse
import json
import shlex
import subprocess
import tempfile
from pathlib import Path

from fastapi.openapi.utils import get_openapi

from app.main import app


def generate_openapi_schema() -> dict:
    return get_openapi(
        title=app.title,
        version=app.version or "0.1.0",
        description=app.description,
        routes=app.routes,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate TypeScript types from FastAPI OpenAPI schema."
    )
    parser.add_argument(
        "--output",
        default="../frontend/lib/api/generated.ts",
        help="Output path for generated TypeScript definitions.",
    )
    parser.add_argument(
        "--generator-cmd",
        default="bunx openapi-typescript",
        help="Command used to generate TypeScript types from OpenAPI JSON.",
    )
    parser.add_argument(
        "--keep-openapi-json",
        default=None,
        help="Optional path to save the intermediate OpenAPI JSON schema.",
    )
    args = parser.parse_args()

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    schema = generate_openapi_schema()

    if args.keep_openapi_json:
        keep_path = Path(args.keep_openapi_json).expanduser()
        keep_path.parent.mkdir(parents=True, exist_ok=True)
        keep_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

    with tempfile.TemporaryDirectory() as temp_dir:
        schema_path = Path(temp_dir) / "openapi.json"
        schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

        cmd = shlex.split(args.generator_cmd) + [
            str(schema_path),
            "--output",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError as exc:
            raise SystemExit(
                "Type generator command not found. Install openapi-typescript or "
                "set --generator-cmd to a valid command."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise SystemExit(f"Type generation failed: {exc}") from exc

    print(f"Generated OpenAPI TypeScript types at {output_path}")


if __name__ == "__main__":
    main()
