from django.test import TestCase
from django_mariadb_vector.fields import MariaVectorField

class FieldTest(TestCase):
    def test_db_type(self):
        field = MariaVectorField()
        self.assertEqual(field.db_type(None), 'VECTOR')
