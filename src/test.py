import pytest

pytest_args = [
    "./tests",
    "--capture=no",
    # other tests here...
]
pytest.main(pytest_args)
