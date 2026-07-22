from __future__ import annotations

import gzip
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import snowflake.connector
from snowflake.connector import DictCursor

from joblytics.core.config.settings import Settings
from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.infrastructure.repositories.errors import SnowflakeLoadError


class SnowflakeRawJobOfferRepository:
    """Persists RawJobOffer batches, unmodified, into Snowflake's RAW (Bronze) layer."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the repository with Snowflake connection settings.

        Args:
            settings (Settings): Application settings holding Snowflake
                credentials and the RAW ingestion landing target
                (database/schema/stage/table).

        Returns:
            None: This method does not return a value.
        """
        self._settings = settings

    def save_batch(self, offers: Sequence[RawJobOffer]) -> int:
        """
        Persist a batch of raw job offers into the Snowflake RAW table.

        Serializes each offer to a line of NDJSON, uploads the batch to the
        configured internal stage via PUT, then loads it into the RAW table
        via COPY INTO. The JSON payload is stored unmodified in a single
        VARIANT column (Bronze layer semantics) — no reshaping happens here.

        Args:
            offers (Sequence[RawJobOffer]): Validated raw job offers to persist.

        Returns:
            int: Number of rows actually loaded, as reported by COPY INTO.

        Raises:
            SnowflakeLoadError: If the PUT or COPY INTO step fails.
        """
        if not offers:
            return 0

        stage = (
            f"@{self._settings.SNOWFLAKE_DATABASE}."
            f"{self._settings.SNOWFLAKE_SCHEMA}."
            f"{self._settings.SNOWFLAKE_STAGE}"
        )
        table = (
            f"{self._settings.SNOWFLAKE_DATABASE}."
            f"{self._settings.SNOWFLAKE_SCHEMA}."
            f"{self._settings.SNOWFLAKE_TABLE}"
        )

        local_path = self._write_ndjson_gzip(offers)

        try:
            with snowflake.connector.connect(
                account=self._settings.SNOWFLAKE_ACCOUNT,
                user=self._settings.SNOWFLAKE_USER,
                password=self._settings.SNOWFLAKE_PASSWORD,
                role=self._settings.SNOWFLAKE_ROLE,
                warehouse=self._settings.SNOWFLAKE_WAREHOUSE,
                database=self._settings.SNOWFLAKE_DATABASE,
                schema=self._settings.SNOWFLAKE_SCHEMA,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"put file://{local_path} {stage} "
                        "auto_compress=false overwrite=false"
                    )

                with connection.cursor(DictCursor) as dict_cursor:
                    dict_cursor.execute(
                        f"copy into {table} (src_json) "
                        f"from {stage}/{local_path.name} "
                        "file_format = (type = json) "
                        "on_error = 'abort_statement'"
                    )
                    rows: list[dict[str, Any]] = dict_cursor.fetchall()
        except Exception as exc:
            raise SnowflakeLoadError(stage=stage, table=table, cause=exc) from exc
        finally:
            local_path.unlink(missing_ok=True)

        return sum(int(row["rows_loaded"]) for row in rows)

    def _write_ndjson_gzip(self, offers: Sequence[RawJobOffer]) -> Path:
        """
        Serialize a batch of raw job offers to a gzip-compressed NDJSON file.

        Args:
            offers (Sequence[RawJobOffer]): Validated raw job offers to serialize.

        Returns:
            Path: Path to the local gzip-compressed NDJSON file.
        """
        provider = offers[0].provider
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{provider}_{timestamp}_{uuid.uuid4().hex}.json.gz"
        local_path = Path(tempfile.gettempdir()) / filename

        with gzip.open(local_path, "wt", encoding="utf-8") as fh:
            for offer in offers:
                fh.write(json.dumps(offer.model_dump(mode="json")) + "\n")

        return local_path
