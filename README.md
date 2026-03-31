# Django MariaDB Vector

Django ORM support for the MariaDB Vector field (introduced in MariaDB 11.7+).

## Why this project exists

MariaDB introduced **native vector support**, allowing you to store embeddings and perform similarity search directly in the database.

However, Django currently lacks:
- a native `VECTOR` model field
- ORM support for vector queries
- automatic migration support for vector indexes

This project fills that gap by providing a clean, Django-native way to work with MariaDB vectors.

## Features

- Django `MariaDBVectorField` for `VECTOR(n)`
- Automatic Django migrations
- Automatic `VECTOR INDEX` creation
- ORM-friendly similarity queries
- Recommendation Manager for Django models
- No raw SQL required
- Works with MariaDB 11.8.2+
- Optionally [optimization for better performance](assets/images/perf_v0.2.0_sm.png) when working with vectors with use package `orjson` and `binary_responce` option


## Why use this

Without this package, using MariaDB vectors in Django requires:

- manual SQL migrations
- custom query expressions
- fragile schema management

With this package, you get:

- clean Django models
- automatic schema generation
- reusable and maintainable code

## Use cases

This package is useful for:

- Retrieval-Augmented Generation (RAG)
- semantic search
- recommendation systems
- document / code similarity search

Typical workflow: text → embedding → store → similarity search

## How it works
- Maps Django field → VECTOR(n)
- Extends Django migration system
- Injects MariaDB-specific SQL for:
- vector columns
- vector indexes
- Wraps vector distance functions like:
  - VEC_DISTANCE
  - VEC_DISTANCE_COSINE
  - VEC_DISTANCE_EUCLIDEAN
- Recommendation Manager (bonus)

## Requirements

- Python 3.12+
- Django 5.2+, or 6.0+
- MariaDB 11.8.2 or newer

## Installation

```bash
pip install django-mariadb-vector
```

### Optional: faster JSON serialization
For better performance when working with vectors, install with the orjson extra:
```bash
pip install django-mariadb-vector[orjson]
```

## Usage

models.py:
```python
from django.db import models
from django_mariadb_vector import MariaDBVectorField, MariaDBVectorIndex


class MyModel(models.Model):
    embedding = MariaDBVectorField(dimensions=3)

    class Meta:
        indexes = [
            # Vector index (MariaDB 11.8.2+)
            MariaDBVectorIndex(fields=["embedding"], dimensions=3)
        ]
```

### Querying with Vector Functions

You can use `VecDistance` to perform similarity searches.

```python
from django_mariadb_vector import VecDistance

from .models import MyModel

# Find 5 most similar records to a reference vector
reference_vector = [0.1, 0.2, 0.3]
results = MyModel.objects.annotate(
    distance=VecDistance("embedding", reference_vector)
).order_by("distance")[:5]
```

### Optimization: `orlson` for better performance
in case of installation `django-mariadb-vector` library with extra `orjson` depencedcy
```bash
pip install django-mariadb-vector[orjson]
```
or 
```bash
uv add django-mariadb-vector[orjson]
```
#### Benefits orlson vs json (batch mode)
- Up to **~20× faster** compared to the standard `json` library on generate vector data
- Up to **~8× faster** compared to the standard `json` library on response vector data

> **Note:** Performance was measured using 20,000 iterations (3 runs) in  
> `tests/test_performance.py`, with randomly generated vectors of dimension 3072.


### Optimization: `binary_response` for better performance

The `binary_response` option improves performance when working with vectors by returning data in a compact binary format instead of JSON.

- Vectors are returned as a sequence of **little-endian IEEE 754 float32 bytes** (4 bytes per value)  
  ([MariaDB reference](https://mariadb.com/docs/server/reference/sql-functions/vector-functions/vec_fromtext))
- Reduces network traffic between MariaDB and your application
- Eliminates JSON parsing overhead on the Python side

#### Benefits of binary response (batch mode)

- Up to **~16× faster** compared to the standard `json` library
- About **~2× faster** compared to `orjson`
- Lower bandwidth usage for large vector payloads

> **Note:** Performance was measured using 20,000 iterations (3 runs) in  
> `tests/test_performance.py`, with randomly generated vectors of dimension 3072.

#### Usage of `binary_response`

```python
from django.db import models
from django_mariadb_vector import MariaDBVectorField

class MyModel(models.Model):
    embedding = MariaDBVectorField(dimensions=3, binary_response=True)
```


### Recommendation Manager for Django models

Using a `RecommendationManager` can simplify vector searches in your application:

models.py:
```python
from django.db import models

from django_mariadb_vector import MariaDBVectorField, MariaDBVectorIndex
from django_mariadb_vector.managers import RecommendationManager


class MyModel(models.Model):
    embedding = MariaDBVectorField(dimensions=3)
    
    objects = RecommendationManager(vector_field="embedding")
    
    class Meta:
        indexes = [
            # Vector index (MariaDB 11.8.2+)
            MariaDBVectorIndex(fields=["embedding"], dimensions=3, m=16),
        ]
```


#### Example of usage Manager
```python
from .models import MyModel

reference_vector:list[float] = [0.1, 0.2, 0.3]

# Find 5 most similar records to a reference vector
results = MyModel.objects.similar_to_vector(reference_vector, limit=5)

for item in results:
    print(f"{item.name} - Distance: {item.distance}")
```

```python
from .models import MyModel

reference_id:int = 1
# Find 5 most similar records to a reference object by id
results = MyModel.objects.similar_to(reference_id, limit=5)

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

## Demo 
A minimal demo project showing how to build article recommendations using vector similarity in Django with MariaDB as the database using the `django-mariadb-vector` library.

- Demo repo: https://github.com/lexxai/django-mariadb-vector-demo
- Example: https://github.com/lexxai/django-mariadb-vector-demo/tree/main/docs


## Docker Testing

You can test the build and run tests in Docker for different Python versions and OS images.
The Dockerfile is located in `tests/docker/Dockerfile`.

### Using the helper script (Linux/macOS)
```bash
bash tests/docker/run_docker_tests.sh
```

### Manual build example
```bash
docker build --build-arg PYTHON_VERSION=3.13 -f tests/docker/Dockerfile -t django-mariadb-vector:test-3.13 .
docker run --rm django-mariadb-vector:test-3.13
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
