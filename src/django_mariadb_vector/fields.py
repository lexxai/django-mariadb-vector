try:
    from orjson import orjson

    HAS_ORJSON = True
except ImportError:
    import json

    HAS_ORJSON = False
import logging
from struct import unpack
from enum import StrEnum

from django.db import models
from django.db.models import Index

logger = logging.getLogger(__name__)


class VectorDistances(StrEnum):
    EUCLIDEAN = "euclidean"
    COSINE = "cosine"


class MariaDBVectorField(models.Field):
    """
    Custom Django model field designed for storing vector embeddings in
    MariaDB 11.8+ compatible databases.

    This class extends the Django models.Field to provide native support
    for vector data types. It automatically handles the serialization of
    vector lists into JSON strings for storage and deserialization back to
    Python lists upon retrieval. The field enforces strict constraints
    by defaulting null and blank options to False to ensure data integrity
    for vector embeddings. It allows configuration of the vector dimension
    size to match specific model requirements.

    :ivar dimensions: Specifies the size of the vector space supported by
                      the field. Default is 768.
    :type dimensions: int
    """

    description = "Vector field for MariaDB 11.8+"

    def __init__(self, dimensions: int = 768, binary_response: bool = False, *args, **kwargs):
        self.dimensions = dimensions
        self.binary_response = binary_response
        kwargs.pop("null", None)  # force always False
        kwargs.pop("blank", None)  # force always False
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        """for automatic migrations Django"""
        name, path, args, kwargs = super().deconstruct()
        kwargs["dimensions"] = self.dimensions
        return name, path, args, kwargs

    def db_type(self, conn):
        return f"VECTOR({self.dimensions})"

    def from_db_value(self, value, expression, conn):
        match value:
            case None | list():
                return value

            case bytes() as b:
                len_value = len(b)
                if len_value != self.dimensions * 4:
                    raise ValueError(f"Invalid vector length: {len_value} bytes, expected {self.dimensions * 4}")

                # Unpack and clean up binary noise
                return [round(f, 7) for f in unpack(f"<{self.dimensions}f", b)]

            case str() as s if s.startswith("["):
                # Use orjson if available, otherwise fallback to standard json
                if HAS_ORJSON:
                    return orjson.loads(value.encode())
                return json.loads(value)

            case _:
                return value

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, (list, tuple)):
            # Auto-resize vector if dimension mismatch
            if len(value) != self.dimensions:
                logger.warning(
                    f"Vector dimension mismatch: expected {self.dimensions}, "
                    f"got {len(value)}. Auto-resizing to zero vector."
                )
                # Return zero vector with correct dimensions
                value = [0.0] * self.dimensions
            if HAS_ORJSON:
                return orjson.dumps(value, option=orjson.OPT_NON_STR_KEYS).decode()
            return json.dumps(value, separators=(",", ":"), allow_nan=False)
        return value

    @staticmethod
    def get_placeholder(value, compiler, conn):
        """Use VEC_FromText() function for inserting/updating"""
        return "VEC_FromText(%s)"

    def select_format(self, compiler, sql, params):
        if self.binary_response:
            return sql, params
        """Automatically wrap field in VEC_ToText() when selecting"""
        return f"VEC_ToText({sql})", params


class MariaDBVectorIndex(Index):
    """
    Index VECTOR for MariaDB.
    Use CREATE INDEX IF NOT EXISTS for CI/CD.
    """

    def __init__(self, *args, m=7, distance=VectorDistances.COSINE, dimensions=768, **kwargs):
        self.m = m
        self.distance = distance
        self.dimensions = dimensions  # for recreating index when changed dimensions
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        path, expressions, kwargs = super().deconstruct()
        kwargs["m"] = self.m
        kwargs["distance"] = self.distance
        kwargs["dimensions"] = self.dimensions
        return path, expressions, kwargs

    def create_sql(self, model, schema_editor, using="", **kwargs):
        """
        Generate SQL for creating a vector index with MariaDB syntax.
        """
        if schema_editor.connection.vendor != "mysql":
            # For testing with non-MariaDB backends, fallback to standard Index
            return super().create_sql(model, schema_editor, using=using, **kwargs)

        table = model._meta.db_table
        column = self.fields[0]

        # Ensure a DYNAMIC row format first
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table} ROW_FORMAT=DYNAMIC")

        # Format: CREATE VECTOR INDEX index_name ON table(column) DISTANCE=metric M=value
        sql = (
            f"CREATE VECTOR INDEX IF NOT EXISTS {self.name} "
            f"ON {table} ({column}) "
            f"DISTANCE={self.distance} M={self.m}"
        )

        return sql


def warmup_vector_index(table_name, column_name):
    """
    VEC_DISTANCE with zero value for force reindex.
    """
    from django.db import connection

    with connection.cursor() as cursor:
        # Simple scan to force an index load
        logger.info(f"--- Warming up index for {table_name}.{column_name} ---")
        response = cursor.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT {column_name} FROM {table_name} 
                ORDER BY VEC_DISTANCE({column_name}, VEC_FromText('[0]')) 
                LIMIT 100
            ) AS warmup;
        """
        )
        return response


MARIADB_MIN_VERSION = (11, 8, 2)


def check_mariadb_version(min_version=MARIADB_MIN_VERSION):
    """Check MariaDB version using Django ORM introspection."""
    from django.db import connection

    # Get version tuple from Django connection
    if connection.vendor != "mysql":
        raise ValueError("VECTOR support requires a MySQL database backend")

    version_tuple = connection.mysql_version
    # Ensure min_version is a tuple for comparison
    if isinstance(min_version, str):
        min_version_tuple = tuple(int(x) for x in min_version.split("."))
    else:
        min_version_tuple = min_version

    # logger.debug(f"MariaDB version: {version_tuple}")

    if version_tuple < min_version_tuple:
        version_str = ".".join(str(x) for x in version_tuple)
        min_version_str = ".".join(str(x) for x in min_version_tuple)
        raise ValueError(
            f"MariaDB version {version_str} is below required version {min_version_str} for VECTOR support"
        )
