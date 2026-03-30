import importlib.metadata


from .fields import MariaDBVectorField, MariaDBVectorIndex, VectorDistances
from .functions import VecFromText, VecToText, VecDistanceCosine, VecDistanceEuclidean, Search, VecDistance


try:
    __version__ = importlib.metadata.version("django-mariadb-vector")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.1"

__all__ = [
    "VectorDistances",
    "MariaDBVectorField",
    "MariaDBVectorIndex",
    "VecFromText",
    "VecToText",
    "VecDistanceCosine",
    "VecDistanceEuclidean",
    "Search",
    "VecDistance",
    "__version__",
]
