import importlib
import json
import random
import sys
import timeit
import unittest
from struct import pack
from time import sleep
from unittest.mock import patch

from django_mariadb_vector import MariaDBVectorField, fields
from django_mariadb_vector.fields import HAS_ORJSON


class TestPerformanceCase(unittest.TestCase):
    dimensions: int = 3072
    iterations: int = 20_000
    repeat: int = 3
    value: list[float]
    value_bytes: bytes
    value_json_str: str

    @classmethod
    def setUpClass(cls):
        cls.value = [random.random()] * cls.dimensions
        cls.value_bytes = pack(f"<{cls.dimensions}f", *cls.value)
        cls.value_json_str = json.dumps(cls.value, allow_nan=False)
        print("Warming for 3 seconds")
        sleep(3)

    def setUp(self):
        importlib.reload(fields)

    def decode_binary(self):
        print("decode_binary start testing...")

        vector_field_binary = MariaDBVectorField(dimensions=self.dimensions)

        def time_bin_decode():
            vector_field_binary.from_db_value(self.value_bytes, None, None)

        time_per_runs = timeit.repeat(stmt=time_bin_decode, number=self.iterations, repeat=self.repeat)
        time_per_run = sum(time_per_runs) / len(time_per_runs)
        print("binary:", time_per_run, time_per_runs)
        return time_per_run

    def decode_json_str(self):
        print("decode_json_str start testing...")

        with patch.dict(sys.modules, {"orjson": None}):
            importlib.reload(fields)
            vector_field_binary = MariaDBVectorField(dimensions=self.dimensions)

            def time_json_str_decode():
                vector_field_binary.from_db_value(self.value_json_str, None, None)

            time_per_runs = timeit.repeat(stmt=time_json_str_decode, number=self.iterations, repeat=self.repeat)
        time_per_run = sum(time_per_runs) / len(time_per_runs)
        print("json_str:", time_per_run, time_per_runs)
        return time_per_run

    def decode_orjson_str(self):
        if not HAS_ORJSON:
            print(
                "orjson is not installed, skipped. \nCan be installed with `uv sync --extra=orjson` or `pip install orjson`"
            )
            return None
        print("decode_orjson_str start testing...")
        vector_field_binary = MariaDBVectorField(dimensions=self.dimensions)

        def time_json_str_decode():
            vector_field_binary.from_db_value(self.value_json_str, None, None)

        time_per_runs = timeit.repeat(stmt=time_json_str_decode, number=self.iterations, repeat=self.repeat)
        time_per_run = sum(time_per_runs) / len(time_per_runs)
        print("json_str:", time_per_run, time_per_runs)
        return time_per_run

    def encode_json_str(self) -> float:
        print("encode_json_str start testing...")
        with patch.dict(sys.modules, {"orjson": None}):
            importlib.reload(fields)

            vector_field_binary = MariaDBVectorField(dimensions=self.dimensions, binary_response=False)

            def time_json_str_encode():
                vector_field_binary.get_prep_value(self.value)

            time_per_runs = timeit.repeat(stmt=time_json_str_encode, number=self.iterations, repeat=self.repeat)

        time_per_run = sum(time_per_runs) / len(time_per_runs)
        print("json_str:", time_per_run, time_per_runs)
        return time_per_run

    def encode_orjson_str(self) -> float | None:
        if not HAS_ORJSON:
            print(
                "orjson is not installed, skipped. \nCan be installed with `uv sync --extra=orjson` or `pip install orjson`"
            )
            return None
        print("encode_orjson_str start testing...")
        vector_field_binary = MariaDBVectorField(dimensions=self.dimensions, binary_response=False)

        def time_json_str_encode():
            vector_field_binary.get_prep_value(self.value)

        time_per_runs = timeit.repeat(stmt=time_json_str_encode, number=self.iterations, repeat=self.repeat)

        time_per_run = sum(time_per_runs) / len(time_per_runs)
        print("orjson_str:", time_per_run, time_per_runs)
        return time_per_run

    def test_decode(self):
        decode_binary_time = self.decode_binary()
        decode_orjson_str_time = self.decode_orjson_str()
        decode_json_str_time = self.decode_json_str()

        print(f"* decode binary is fastest than json in {decode_json_str_time / decode_binary_time:.2f} times")

        if decode_orjson_str_time:
            print(f"* decode binary is fastest than orjson in {decode_orjson_str_time / decode_binary_time:.2f} times")

            print(f"* decode orjson is fastest than json in {decode_json_str_time/decode_orjson_str_time:.2f} times")

    def test_encode_str(self):
        orjson_time = self.encode_orjson_str()
        json_time = self.encode_json_str()
        if orjson_time:
            print(f"* encode orjson is fastest than json in {json_time/orjson_time:.2f} times")


if __name__ == "__main__":
    unittest.main()
