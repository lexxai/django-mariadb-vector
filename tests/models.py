from django.db import models
from django_mariadb_vector.fields import MariaDBVectorField, MariaDBVectorIndex


class VectorModel(models.Model):
    embedding = MariaDBVectorField(dimensions=3)

    class Meta:
        indexes = [MariaDBVectorIndex(fields=["embedding"], dimensions=3)]


class VectorModelBinary(models.Model):
    embedding = MariaDBVectorField(dimensions=3, binary_response=True)

    class Meta:
        indexes = [MariaDBVectorIndex(fields=["embedding"], dimensions=3)]
