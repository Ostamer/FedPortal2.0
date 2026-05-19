import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.clients.fed_portal import ExternalApiClient
from src.config.main import settings
from src.consumers.consumer import MessageConsumer
from src.config.logging import setup_logging, get_logger
from src.routers.sync import sync_router
from src.models.base import engine

setup_logging()
logger = get_logger(__name__)


async def consumer_wrapper(consumer: MessageConsumer):
    try:
        await consumer.start()
    except asyncio.CancelledError:
        logger.info("consumer_task_cancelled")
        raise
    except Exception as exc:
        logger.critical("consumer_crashed", error=str(exc))
        raise


async def startup(app: FastAPI):
    logger.info("app_starting", name=settings.app_name)

    app.state.client = ExternalApiClient(
        base_url=settings.fed_portal_api_url,
        api_key=settings.fed_portal_api_key,
        host=settings.fed_portal_api_host,
    )
    logger.info("external_api_client_created")

    consumer = MessageConsumer(app.state.client)
    app.state.consumer = consumer
    app.state.consumer_task = asyncio.create_task(consumer_wrapper(consumer))
    logger.info("consumer_started")


async def shutdown(app: FastAPI):
    logger.info("app_stopping")

    consumer_task = getattr(app.state, 'consumer_task', None)
    if consumer_task and not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("consumer_task_awaited")

    consumer = getattr(app.state, 'consumer', None)
    if consumer:
        await consumer.stop()

    await engine.dispose()
    logger.info("database_disconnected")

    client = getattr(app.state, 'client', None)
    if client:
        await client.close()
        logger.info("external_api_client_closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup(app)
    yield
    await shutdown(app)


app = FastAPI(
    title=settings.app_name,
    description="Сервис для отправки данных на федеральный портал",
    lifespan=lifespan,
)


@app.get('/health/')
async def health():
    return {'status': 'ok'}


app.include_router(sync_router, prefix="/sync")
