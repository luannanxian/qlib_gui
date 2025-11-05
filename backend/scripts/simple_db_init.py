"""
Simple MySQL Database Initialization
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# MySQL connection details
DATABASE_URL = "mysql+aiomysql://remote:remote123456@192.168.3.46:3306/qlib_ui?charset=utf8mb4"


async def test_and_create():
    """Test connection and create database"""
    print("=" * 60)
    print("MySQL Database Initialization")
    print("=" * 60)

    # Step 1: Test connection to MySQL server
    print("\n1. Testing MySQL server connection...")
    base_url = "mysql+aiomysql://remote:remote123456@192.168.3.46:3306/mysql?charset=utf8mb4"
    engine = create_async_engine(base_url, echo=False)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"   ✅ Connected to MySQL {version}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    finally:
        await engine.dispose()

    # Step 2: Create database
    print("\n2. Creating database 'qlib_ui'...")
    try:
        engine = create_async_engine(base_url, echo=False)
        async with engine.begin() as conn:
            await conn.execute(
                text("CREATE DATABASE IF NOT EXISTS qlib_ui CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            )
            print("   ✅ Database created or already exists")

            # Verify
            result = await conn.execute(text("SHOW DATABASES LIKE 'qlib_ui'"))
            if result.scalar():
                print("   ✅ Database verified")
            else:
                print("   ❌ Database not found")
                return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    finally:
        await engine.dispose()

    # Step 3: Create tables
    print("\n3. Creating tables...")
    try:
        from app.database.base import Base

        engine = create_async_engine(DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            # Drop existing tables
            print("   Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)

            # Create all tables
            print("   Creating tables...")
            await conn.run_sync(Base.metadata.create_all)

        # Verify tables
        async with engine.begin() as conn:
            result = await conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"   ✅ Tables created: {', '.join(tables)}")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    print(f"\nDatabase: qlib_ui @ 192.168.3.46:3306")
    print(f"Tables: {', '.join(tables)}")
    print("\nYou can now start using the database.")

    return True


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/Users/zhenkunliu/project/qlib-ui/backend")

    success = asyncio.run(test_and_create())
    sys.exit(0 if success else 1)
