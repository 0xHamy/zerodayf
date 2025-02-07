import asyncio
from database import create_tables, empty_tables

async def main(action: str):
    if action == "create":
        await create_tables()
    elif action == "reset":
        await empty_tables()
    else:
        raise ValueError("Use 'create' or 'reset'")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python manage_db.py [create|reset]")
        sys.exit(1)
    
    asyncio.run(main(sys.argv[1]))

