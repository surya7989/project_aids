import sys
import os
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

from backend.config.settings import settings
from backend.main import app
from mangum import Mangum


def create_tables():
    try:
        from backend.database.session import Base
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(settings.get_database_url(), echo=False)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def init():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await engine.dispose()
        loop.run_until_complete(init())
        loop.close()
    except Exception as e:
        print(f"Warning: could not create tables: {e}")


create_tables()


handler = Mangum(app, lifespan="off")
