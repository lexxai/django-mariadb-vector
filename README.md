# Django MariaDB Vector

Django ORM support for the MariaDB Vector field (introduced in MariaDB 11.8.2).

## Requirements

- Python 3.12+
- Django 5.2+, or 6.0+
- MariaDB 11.8.2 or newer

## Installation

```bash
pip install django-mariadb-vector
```

## Usage

```python
from django.db import models
from django_mariadb_vector import MariaDBVectorField, MariaDBVectorIndex


class MyModel(models.Model):
    embedding = MariaDBVectorField(dimensions=1536)

    class Meta:
        indexes = [
            # Vector index (MariaDB 11.8.2+)
            MariaDBVectorIndex(fields=["embedding"], name="v_idx", dimensions=1536),
        ]
```

### Querying with Vector Functions

You can use `Search` (which uses `VEC_DISTANCE_COSINE` by default) or `VecDistance` to perform similarity searches.

```python
from django_mariadb_vector import Search

from .models import MyModel

# Find 5 most similar records to a reference vector
reference_vector = [0.1, 0.2, 0.3, ...]
results = MyModel.objects.annotate(
    distance=Search("embedding", reference_vector)
).order_by("distance")[:5]
```

### Recommended Manager Pattern

Using a custom manager can simplify vector searches in your application:

```python
from django.db import models
from django_mariadb_vector import MariaDBVectorField, Search

class RecommendationManager(models.Manager):
    def similar_to_vector(self, vector, limit=5, exclude_id=None):
        queryset = self.get_queryset().annotate(
            distance=Search("embedding", vector)
        ).order_by("distance")

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        return queryset[:limit]

    def similar_to(self, id: int, limit=5):
        try:
            vector = self.get_queryset().values_list("embedding", flat=True).get(id=id)
        except self.model.DoesNotExist:
            return self.get_queryset().none()
        
        # Pass the ID to similar_to_vector to exclude it there
        return self.similar_to_vector(vector, limit=limit, exclude_id=id)

class MyModel(models.Model):
    embedding = MariaDBVectorField(dimensions=1536)
    objects = RecommendationManager()
```

#### Example of usage Manager
```python
from .models import MyModel

reference_vector:list[float] = [0.1, 0.2, 0.3, ...]

# Find 5 most similar records to a reference vector
results = MyModel.objects.similar_to_vector(reference_vector, limit=5)

for item in results:
    print(f"{item.name} - Distance: {item.distance}")
```

```python
from .models import MyModel

reference_vector:int = 1
# Find 5 most similar records to a reference object by id
results = MyModel.objects.similar_to(reference_vector, limit=5)

for item in results:
    print(f"{item.name} - Distance: {item.distance}")
```

### Advanced Functions

The following functions are available in `django_mariadb_vector.functions`:

- `Search(expression, vector)`: Convenient wrapper for COSINE distance search.
- `VecDistance(expression, vector)`: Generic `VEC_DISTANCE` function.
- `VecDistanceCosine(expression, vector)`: Native MariaDB `VEC_DISTANCE_COSINE`.
- `VecDistanceEuclidean(expression, vector)`: Native MariaDB `VEC_DISTANCE_EUCLIDEAN`.
- `VecFromText(text)`: Converts JSON string to MariaDB VECTOR format.
- `VecToText(expression)`: Converts MariaDB VECTOR format to JSON string.

## Reference
- https://mariadb.com/docs/server/reference/sql-functions/vector-functions

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
