import importlib
import sys
from struct import pack
from unittest.mock import patch

from django.test import TestCase
from django.db import connection
from django_mariadb_vector import MariaDBVectorField, MariaDBVectorIndex, __version__, fields
from django_mariadb_vector.fields import HAS_ORJSON
from django_mariadb_vector.functions import Search, VecDistance
from .models import VectorModel, VectorModelBinary

print(f"Running tests with django-mariadb-vector version: {__version__}")


class FieldTest(TestCase):
    def setUp(self):
        self.binary_response = True

    def test_db_type(self):
        field = MariaDBVectorField(dimensions=1536)
        self.assertEqual(field.db_type(connection), "VECTOR(1536)")

    def test_get_prep_value(self):
        field = MariaDBVectorField(dimensions=3)
        self.assertEqual(field.get_prep_value([1.0, 2.0, 3.0]), "[1.0,2.0,3.0]")
        # Test auto-resize with warning (we just check it returns zero vector)
        self.assertEqual(field.get_prep_value([1.0, 2.0]), "[0.0,0.0,0.0]")

    def test_deconstruct(self):
        field = MariaDBVectorField(dimensions=100)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(kwargs["dimensions"], 100)

    def from_db_value_str(self):
        importlib.reload(fields)

        field = MariaDBVectorField(dimensions=3)
        self.assertEqual(field.from_db_value("[1.0,2.0,3.0]", None, None), [1.0, 2.0, 3.0])

    def test_from_db_value_str_json(self):
        print("decode_json_str start testing...")
        with patch.dict(sys.modules, {"orjson": None}):
            self.from_db_value_str()

    def test_from_db_value_str_orjson(self):
        if not HAS_ORJSON:
            self.skipTest(
                "orjson is not installed, skipped. \nCan be installed with `uv sync --extra=orjson` or `pip install orjson`"
            )
        print("decode_orjson_str start testing...")
        self.from_db_value_str()

    def test_from_db_value_binary(self):
        values = [1.0, 2.0, 3.0]
        field = MariaDBVectorField(dimensions=len(values))
        value_bytes = pack(f"<{field.dimensions}f", *values)
        self.assertEqual(field.from_db_value(value_bytes, None, None), values)

    def test_select_format_str(self):
        field = MariaDBVectorField(binary_response=False)
        value = "JSON"
        response, _ = field.select_format(None, "JSON", None)  # noqa
        self.assertEqual(response, f"VEC_ToText({value})")

    def test_select_format_binary(self):
        field = MariaDBVectorField(binary_response=True)
        value = b"\x00\x00\x00\x00"  # A simple 4-byte float representation (0.0)
        response, _ = field.select_format(None, value, None)  # noqa
        self.assertEqual(response, value)


class IndexTest(TestCase):
    def test_deconstruct(self):
        index = MariaDBVectorIndex(fields=["embedding"], name="idx", dimensions=3, m=5)
        path, expressions, kwargs = index.deconstruct()
        self.assertEqual(kwargs["dimensions"], 3)
        self.assertEqual(kwargs["m"], 5)


class FunctionTest(TestCase):
    def test_search_sql(self):
        from django.db.models import F

        query = VectorModel.objects.annotate(dist=Search("embedding", [1.0, 2.0, 3.0])).values("dist")
        sql, params = query.query.sql_with_params()
        # Note: SQLite backend will be used in tests, so we just check if it compiles
        self.assertIn("VEC_DISTANCE_COSINE", sql)
        self.assertIn("VEC_FromText", sql)

    def test_vector_distance_sql(self):
        query = VectorModel.objects.annotate(dist=VecDistance("embedding", [1.0, 2.0, 3.0])).values("dist")
        sql, params = query.query.sql_with_params()
        self.assertIn("VEC_DISTANCE", sql)


from unittest import skipIf


@skipIf(connection.vendor != "mysql", "Backend engine is not MySQL/MariaDB")
class FillDataTest(TestCase):
    def test_fill_and_read_vector_data(self):
        values = [1.0, 2.0, 3.0]
        VectorModel.objects.create(embedding=values)
        obj = VectorModel.objects.first()
        self.assertEqual(obj.embedding, values)

    def test_fill_and_read_vector_data_binary(self):
        values = [1.0, 2.0, 3.0]
        VectorModelBinary.objects.create(embedding=values)
        obj = VectorModelBinary.objects.first()
        self.assertEqual(obj.embedding, values)
