from django.test import TestCase
from django.db import connection
from django_mariadb_vector import MariaDBVectorField, MariaDBVectorIndex, __version__
from django_mariadb_vector.functions import Search, VecDistance
from .models import VectorModel

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
