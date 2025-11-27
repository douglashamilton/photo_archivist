import asyncio
import inspect


def pytest_pyfunc_call(pyfuncitem):
    if asyncio.iscoroutinefunction(pyfuncitem.obj):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            sig = inspect.signature(pyfuncitem.obj)
            accepted = {name: value for name, value in pyfuncitem.funcargs.items() if name in sig.parameters}
            loop.run_until_complete(pyfuncitem.obj(**accepted))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return True
    return None
