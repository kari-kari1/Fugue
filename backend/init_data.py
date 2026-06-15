"""初始化预设数据（模板等）"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.services.template_seeder import seed_templates


async def init():
    """初始化所有预设数据"""
    print("🔄 Initializing preset data...")

    async with AsyncSessionLocal() as db:
        try:
            # 初始化模板
            result = await seed_templates(db)
            print(f"✅ Templates: created={result['total_created']}, skipped={result['total_skipped']}")
        except Exception as e:
            print(f"⚠️ Template seeding error: {e}")

    print("✅ Initialization complete!")


if __name__ == "__main__":
    asyncio.run(init())
