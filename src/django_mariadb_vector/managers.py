from django.db import models
from django.db.models import QuerySet

from .functions import VecDistance


class RecommendationManager(models.Manager):
    """
    Manager for finding records that are closest to a vector embedding.

    This manager provides methods to query objects that are most similar
    to a given vector or to another object in the database, based on
    a vector field (e.g., embeddings) and a distance metric
    """
    def __init__(self, vector_field: str = "embedding", distance: str = "distance"):
        """
        Initialize the RecommendationManager.

        Args:
            vector_field (str): The name of the model field storing vector embeddings.
            distance (str): The annotation key used to store computed distances.
        """
        super().__init__()
        self.vector_field = vector_field
        self.distance = distance

    def similar_to_vector(
        self, vector, limit: int = 5, exclude_id: int = None, with_embedding: bool = False
    ) -> QuerySet:
        """
        Retrieve objects most similar to a given vector.

        Args:
            vector: The reference vector to compare against.
            limit (int): Maximum number of results to return. Defaults to 5.
            exclude_id (int, optional): Primary key of an object to exclude from results.
            with_embedding (bool): Whether to include the embedding field in the results.
                                   Defaults to False (embedding is deferred).

        Returns:
            QuerySet: A queryset of objects ordered by similarity to the given vector.
        """
        annotate_param = {self.distance: VecDistance(self.vector_field, vector)}
        queryset = self.get_queryset().annotate(**annotate_param).order_by(self.distance)

        if not with_embedding:
            queryset = queryset.defer(self.vector_field)

        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)

        return queryset[:limit]

    def similar_to(self, pk: int, limit: int = 5, with_embedding: bool = False) -> QuerySet:
        """
        Retrieve objects most similar to a given object in the database.

        Args:
            pk (int): Primary key of the reference object.
            limit (int): Maximum number of results to return. Defaults to 5.
            with_embedding (bool): Whether to include the embedding field in the results.
                                   Defaults to False (embedding is deferred).

        Returns:
            QuerySet: A queryset of objects ordered by similarity to the reference object.
                      Returns an empty queryset if the object does not exist.
        """
        try:
            vector = self.get_queryset().values_list(self.vector_field, flat=True).get(pk=pk)
        except self.model.DoesNotExist:
            return self.get_queryset().none()

        return self.similar_to_vector(vector, limit=limit, exclude_id=pk, with_embedding=with_embedding)
