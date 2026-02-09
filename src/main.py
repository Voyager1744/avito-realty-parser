from config.settings import settings
from daily_runner import run_forever, run_once


def main():
    if settings.run_mode.lower() == "loop":
        run_forever()
        return 0

    return_code = 0
    try:
        import asyncio

        asyncio.run(run_once())
    except Exception:
        return_code = 1
        raise
    return return_code


if __name__ == "__main__":
    main()
