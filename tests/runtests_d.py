import os

import django
from django.conf import settings
from django.core.management import call_command
from django.test.utils import get_runner

print(f"Docker edition... ")
if not os.getenv("DB_NAME"):
    print(os.environ)
    raise ValueError("DB_NAME environment variable is required for Docker tests")


def run_tests():
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": os.getenv("DB_ENGINE", default="django.db.backends.mysql"),
                    "NAME": os.getenv("DB_NAME"),
                    "USER": os.getenv("DB_USER"),
                    "PASSWORD": os.getenv("DB_PASSWORD"),
                    "HOST": os.getenv("DB_HOST", default="db-unknown"),
                    "PORT": int(os.getenv("DB_PORT", default="3306")),
                    "TEST": {"NAME": os.getenv("DB_NAME")},
                },
            },
            INSTALLED_APPS=[
                "tests",
            ],
            # MIGRATION_MODULES={
            #     "tests": None,
            # },
            SECRET_KEY="fake-key",
        )
    django.setup()

    call_command("makemigrations", "tests", verbosity=1)

    TestRunner = get_runner(settings)
    test_runner = TestRunner(keepdb=True, verbosity=2)
    result_failures = test_runner.run_tests(["tests"])
    return result_failures


if __name__ == "__main__":
    import sys

    failures = run_tests()
    sys.exit(bool(failures))
