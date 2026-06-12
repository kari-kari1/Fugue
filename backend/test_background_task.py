"""测试后台任务是否能正常执行"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_background():
    logger.info("Background task started")
    await asyncio.sleep(1)
    logger.info("Background task completed")


async def main():
    logger.info("Creating background task")
    task = asyncio.create_task(test_background())
    logger.info("Task created, waiting 3 seconds")
    await asyncio.sleep(3)
    logger.info("Main function done")


if __name__ == "__main__":
    asyncio.run(main())
