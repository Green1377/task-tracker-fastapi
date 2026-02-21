import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь поиска модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.library_catalog.external.openlibrary.client import OpenLibraryClient

async def test():
    client = OpenLibraryClient()

    # Тест по ISBN
    data = await client.search_by_isbn("9780132350884")
    print(f"Found: {data}")

    # Тест по title+author
    data = await client.search_by_title_author(
        "Clean Code",
        "Robert Martin"
    )
    print(f"Found: {data}")

    await client.close()


asyncio.run(test())