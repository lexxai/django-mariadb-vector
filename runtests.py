import django
from django.conf import settings
from django.test.utils import get_runner

def run_tests():
    if not settings.configured:
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django_mariadb_vector',
                'tests',
            ],
            MIGRATION_MODULES={
                'tests': None,
            },
            SECRET_KEY='fake-key',
        )
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests"])
    return failures

if __name__ == "__main__":
    import sys
    failures = run_tests()
    sys.exit(bool(failures))
