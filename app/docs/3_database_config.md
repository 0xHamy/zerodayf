# Database Management Guide

## Overview
Zerodayf includes a streamlined database management script for local development and testing purposes. This utility script provides straightforward commands for creating and resetting database tables.

## Location
The database management script is located at:
```
zerodayf/app/models/manage_db.py
```

## Implementation
The script provides an asynchronous implementation for database operations:

```python
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
```

## Usage Instructions
The script accepts two commands:

1. Create tables:
   ```
   python manage_db.py create
   ```

2. Reset (empty) tables:
   ```
   python manage_db.py reset
   ```

If an invalid command is provided, the script will display usage instructions and exit with a status code of 1.

This utility ensures consistent database management across local development environments and simplifies the process of setting up or resetting the application's database state for testing purposes.
