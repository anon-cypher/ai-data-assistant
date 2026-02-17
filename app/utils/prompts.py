class Prompts:
    """Centralized prompt templates accessible as attributes or via `get`."""

    SQL_GENERATION = (
        "Generate PostgreSQL SQL.\n\n"
        "Use only these tables:\n\n{schema_context}\n"
        "Return only SQL.\n\n"
        "Question: {question}\n"
    )

    @classmethod
    def get(cls, name: str) -> str:
        return getattr(cls, name, "")
