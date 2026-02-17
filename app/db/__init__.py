"""Database package for schema inspection and connection utilities.

This package exposes helpers for creating the SQLAlchemy engine,
inspecting schema metadata, and generating a schema metadata JSON file
used by the FAISS index builder.
"""

__all__ = [
	"connection",
	"schema_loader",
	"schema_metadata_generator",
]
