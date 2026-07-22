class SnowflakeLoadError(RuntimeError):
    def __init__(self, stage: str, table: str, cause: Exception):
        self.stage = stage
        self.table = table
        self.cause = cause

        super().__init__(
            f"Failed to load batch into {table} via stage {stage}: {cause}"
        )
