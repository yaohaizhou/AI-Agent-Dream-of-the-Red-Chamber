import asyncio
import inspect


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "asyncio: mark test to run as an async coroutine",
    )


def pytest_pyfunc_call(pyfuncitem):
    testfunction = pyfuncitem.obj
    if not inspect.iscoroutinefunction(testfunction):
        return None

    funcargs = {name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames}
    asyncio.run(testfunction(**funcargs))
    return True
