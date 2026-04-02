"""Embedded sample logs for demos and smoke tests."""

FIXTURES: dict[str, dict[str, str]] = {
    "pytest-import": {
        "title": "Python — ModuleNotFoundError (pytest)",
        "log": r"""
============================= test session starts ==============================
platform linux -- Python 3.11.6, pytest-8.0.0, pluggy-1.4.0
rootdir: /home/runner/work/app/app
collected 12 items

tests/test_api.py::test_health FAILED                                    [  8%]

=================================== FAILURES ===================================
______________________________ test_health ___________________________________

    def test_health():
>       from app.main import app
E       ModuleNotFoundError: No module named 'httpx'

tests/test_api.py:4: ModuleNotFoundError
=========================== short test summary info ============================
FAILED tests/test_api.py::test_health - ModuleNotFoundError: No module named 'httpx'
============================== 1 failed in 0.42s ===============================
""".strip(),
    },
    "jest-typeerror": {
        "title": "JavaScript — TypeError (Jest-style)",
        "log": r"""
FAIL src/services/user.test.ts
  ● UserService › maps profile

    TypeError: Cannot read properties of undefined (reading 'id')

      12 |   const profile = await fetchProfile(userId);
      13 |   return {
    > 14 |     id: profile.id,
         |                 ^
      15 |   };
      16 | };

      at mapUser (src/services/user.ts:14:17)
      at Object.<anonymous> (src/services/user.test.ts:22:11)

Test Suites: 1 failed, 1 total
Tests:       1 failed, 3 passed, 4 total
""".strip(),
    },
    "pytest-assert": {
        "title": "Python — AssertionError (pytest)",
        "log": r"""
tests/unit/test_math.py::test_sum FAILED

=================================== FAILURES ===================================
__________________________________ test_sum ____________________________________

    def test_sum():
>       assert add(2, 2) == 5
E       assert 4 == 5
E        +  where 4 = add(2, 2)

tests/unit/test_math.py:8: AssertionError
""".strip(),
    },
}


def list_fixture_meta() -> list[dict[str, str]]:
    return [{"id": k, "title": v["title"]} for k, v in FIXTURES.items()]


def get_fixture_log(fixture_id: str) -> str:
    if fixture_id not in FIXTURES:
        raise KeyError(fixture_id)
    return FIXTURES[fixture_id]["log"]
