import asyncio
import signal
import sys
from datetime import datetime

from app.config import settings
from app.pipeline.scheduler import scheduler, setup_scheduler

async def main():
    print(f"[{datetime.utcnow().isoformat()}] Standalone scheduler starting...")
    print(f"  debug={settings.debug}")
    if settings.odds_api_key:
        print(f"  Odds API: ...{settings.odds_api_key[-4:]}")
    else:
        print("  WARNING: No ODDS_API_KEY set")

    setup_scheduler()

    jobs = scheduler.get_jobs()
    for j in jobs:
        print(f"  Job: {j.id} | next run: {j.next_run_time}")

    stop_event = asyncio.Event()

    def shutdown():
        print(f"\n[{datetime.utcnow().isoformat()}] Shutting down scheduler...")
        scheduler.shutdown(wait=False)
        stop_event.set()

    if sys.platform == "win32":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, shutdown)
            except NotImplementedError:
                pass
    else:
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                asyncio.get_event_loop().add_signal_handler(sig, shutdown)
            except NotImplementedError:
                pass

    print(f"[{datetime.utcnow().isoformat()}] Scheduler running. Press Ctrl+C to stop.")
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
