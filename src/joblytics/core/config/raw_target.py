from pydantic import BaseModel, ConfigDict, Field


class SnowflakeRawTarget(BaseModel):
    """
    Identifies the Snowflake landing location for one provider's raw (Bronze)
    job offers: database, schema, internal stage, and table.
    """

    model_config = ConfigDict(extra="forbid")

    database: str
    # Named "schema_name", not "schema": a field literally named "schema"
    # shadows a BaseModel attribute and triggers a Pydantic UserWarning.
    schema_name: str
    stage: str
    table: str

    @property
    def stage_ref(self) -> str:
        """
        Fully qualified internal stage reference for PUT/COPY INTO statements.

        Returns:
            str: `@database.schema_name.stage`.
        """
        return f"@{self.database}.{self.schema_name}.{self.stage}"

    @property
    def table_ref(self) -> str:
        """
        Fully qualified table reference for COPY INTO statements.

        Returns:
            str: `database.schema_name.table`.
        """
        return f"{self.database}.{self.schema_name}.{self.table}"


class SnowflakeRawTargetResolver(BaseModel):
    """
    Resolves the Snowflake raw-landing target for a given provider.

    Unlike HttpPolicy's field-level merge, resolution here is a full
    replacement: a provider either gets its own complete SnowflakeRawTarget
    or falls back entirely to the default. Partially merging identifier
    fields (database/schema/stage/table) has no safe "neutral" value — a
    forgotten override could silently misroute one provider's data into
    another provider's table.
    """

    model_config = ConfigDict(extra="forbid")

    default: SnowflakeRawTarget
    per_provider: dict[str, SnowflakeRawTarget] = Field(default_factory=dict)

    def for_provider(self, provider: str) -> SnowflakeRawTarget:
        """
        Resolve the Snowflake raw target for a given provider.

        Args:
            provider (str): Logical provider identifier.

        Returns:
            SnowflakeRawTarget: The provider's own target if configured,
                otherwise the default target.
        """
        return self.per_provider.get(provider, self.default)
