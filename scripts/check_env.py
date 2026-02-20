
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings


with open('env_debug.txt', 'w') as out:
out.write(f"DATABASE_URI from settings: {settings.DATABASE_URI}\n")
out.write(f"POSTGRES_DB from settings: {settings.POSTGRES_DB}\n")
out.write(f"Current working directory: {os.getcwd()}\n")
out.write(f".env file path: {os.path.abspath('.env')}\n")
if os.path.exists('.env'):
out.write(".env file exists\n")
with open('.env', 'r') as f:
out.write(".env content snippet:\n")
for line in f:
if "POSTGRES_DB" in line:
out.write(line)
else:
out.write(".env file DOES NOT exist\n")
