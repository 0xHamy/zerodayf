# Database Management Guide

## Overview
Zerodayf includes a streamlined database management script for local development and testing purposes. This utility script provides straightforward commands for creating and resetting database tables. 

The database management script is located at: `zerodayf/app/models/manage_db.py`

### Usage
You can use it by running it either with reset or create arguments to drop tables or create them:
```
python3 manage_db.py reset
python3 manage_db.py create
```

