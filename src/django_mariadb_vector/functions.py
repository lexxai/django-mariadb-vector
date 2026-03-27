from django.db import models
from django.db.models import Func, BinaryField, FloatField, IntegerField, Value


class VecFromText(Func):
    function = "VEC_FromText"
    template = "%(function)s(%(expressions)s)"
    output_field = BinaryField()


class VecToText(Func):
    function = "VEC_ToText"
    template = "%(function)s(%(expressions)s)"
    output_field = models.TextField()


class VecDistanceCosine(Func):
    """
    The VEC_DISTANCE_COSINE function calculates the cosine distance between two vectors.
    Usage: .annotate(dist=VecDistanceCosine('embedding', Value(VecFromText('[0.1, 0.2, ...]'))))
    """
    function = "VEC_DISTANCE_COSINE"
    output_field = FloatField()


class VecDistanceEuclidean(Func):
    """
    The VEC_DISTANCE_EUCLIDEAN function calculates the cosine distance between two vectors.
    Usage: .annotate(dist=VecDistanceEuclidean('embedding', Value(VecFromText('[0.1, 0.2, ...]'))))
    """
    function = "VEC_DISTANCE_EUCLIDEAN"
    output_field = IntegerField()


class Search(Func):
    function = "VEC_DISTANCE_COSINE"
    output_field = FloatField()

    def __init__(self, expression, reference_vector, **extra):
        import json

        # 1. Convert the list to a JSON string immediately
        if isinstance(reference_vector, (list, tuple)):
            reference_vector = json.dumps(reference_vector)

        # 2. Wrap it in a Value() so Django knows it's a parameter
        super().__init__(expression, Value(reference_vector), **extra)

    def as_sql(self, compiler, connection, **extra_context):
        # Compile the first expression (the column 'embedding')
        lhs_sql, lhs_params = compiler.compile(self.source_expressions[0])

        # Compile the second expression (our JSON string)
        rhs_sql, rhs_params = compiler.compile(self.source_expressions[1])

        # 3. CRITICAL: We use %s inside VEC_FromText.
        # The DB driver will replace %s with '%s' (with quotes) automatically.
        sql = f"{self.function}({lhs_sql}, VEC_FromText({rhs_sql}))"

        return sql, list(lhs_params) + list(rhs_params)


class VecDistance(Func):
    """
    The VEC_DISTANCE function is a generic function that behaves either as VEC_DISTANCE_EUCLIDEAN or VEC_DISTANCE_COSINE, depending on the underlying index type.
    Usage: .annotate(dist=VecDistance('embedding', [0.1, 0.2, ...]))
    """

    function = "VEC_DISTANCE"
    output_field = FloatField()

    def __init__(self, expression, reference_vector, **extra):
        import json

        if isinstance(reference_vector, (list, tuple)):
            reference_vector = json.dumps(reference_vector)
        super().__init__(expression, Value(reference_vector), **extra)

    def as_sql(self, compiler, connection, **extra_context):
        lhs_sql, lhs_params = compiler.compile(self.source_expressions[0])
        rhs_sql, rhs_params = compiler.compile(self.source_expressions[1])
        sql = f"{self.function}({lhs_sql}, VEC_FromText({rhs_sql}))"
        return sql, list(lhs_params) + list(rhs_params)
