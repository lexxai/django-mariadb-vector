# Django MariaDB Vector

Django ORM support for the MariaDB Vector field (introduced in MariaDB 11.8.2).

## Requirements

- Python 3.12+
- Django 5.0, 5.1, or 6.0+
- MariaDB 11.8.2 or newer

## Installation

```bash
pip install django-mariadb-vector
```

## Usage

```python
from django.db import models
from django_mariadb_vector import MariaVectorField, MariaVectorIndex

class MyModel(models.Model):
    context = models.TextField(blank=True, null=True, help_text="Source context for embedding")
    model_name = models.CharField(max_length=100, blank=True, null=True)
    embedding = MariaVectorField(dimensions=1536)
    updated_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        indexes = [
            # Vector index
            MariaVectorIndex(fields=["embedding"],dimensions=1536),
        ]
```

## Optionally can add `RecommendationManager` to model:
```python
from django.db import models
from django_mariadb_vector import MariaVectorField, MariaVectorIndex
from .managers import RecommendationManager

VECTOR_DIMENSIONS=1536

class MyModel(models.Model):
    context = models.TextField(blank=True, null=True, help_text="Source context for embedding")
    model_name = models.CharField(max_length=100, blank=True, null=True)
    embedding = MariaVectorField(dimensions=VECTOR_DIMENSIONS)
    updated_at = models.DateTimeField(null=True, blank=True)
    
    objects = RecommendationManager()

    class Meta:
        indexes = [
            # Vector index
            MariaVectorIndex(fields=["embedding"],dimensions=VECTOR_DIMENSIONS),
        ]
```

managers.py:

```python
import logging

from django.db import models
from django.db.models import QuerySet

from django_mariadb_vector import Search

logger = logging.getLogger(__name__)


class RecommendationManager(models.Manager):
    def similar_to(self, id, limit=5, with_embedding=False) -> QuerySet:
        """
        Finds recommendations similar to a specific id.
        """
        try:
            source_embedding = self.get(id=id).embedding
        except self.model.DoesNotExist:
            return self.none()

        queryset = self.get_queryset().annotate(distance=Search("embedding", source_embedding))

        if not with_embedding:
            queryset = queryset.defer("embedding")

        queryset = queryset.exclude(id=id).order_by("distance")[:limit]

        return queryset
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
