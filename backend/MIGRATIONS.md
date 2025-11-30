# Database Migrations Guide

This project uses **Alembic** for database schema migrations. This allows you to change your database schema without losing data.

## Why Alembic?

- ✅ **Preserves data** when changing database schema
- ✅ **Tracks changes** over time with version control
- ✅ **Allows rollbacks** if something goes wrong
- ✅ **Works seamlessly** with SQLAlchemy

## How to Use Alembic

### Making Changes to the Database Schema

When you modify the database models in `app/models.py`, follow these steps:

#### 1. Create a Migration

After making changes to `app/models.py`, generate a migration file:

```bash
cd backend
alembic revision --autogenerate -m "Description of your changes"
```

Example:
```bash
alembic revision --autogenerate -m "Add dosage_instructions field to Drug"
```

This creates a new migration file in `alembic/versions/` with the changes detected.

#### 2. Review the Migration

**IMPORTANT**: Always review the generated migration file before applying it!

- Check that it's doing what you expect
- Look for any unintended changes
- Make manual edits if needed

#### 3. Apply the Migration

To update your database to the latest version:

```bash
alembic upgrade head
```

This applies all pending migrations.

### Common Commands

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to a specific version
alembic downgrade <revision_id>

# Upgrade to latest
alembic upgrade head
```

## Docker Setup

### Database Persistence

The database is stored in a **Docker named volume** called `medicine-data`. This means:

- ✅ Data persists when containers are stopped/restarted
- ✅ Data persists when containers are rebuilt
- ✅ Data is managed by Docker and backed up with volume backups

### Automatic Migrations on Startup

When you run `docker-compose up`, the backend container automatically:

1. Runs `alembic upgrade head` to apply any pending migrations
2. Starts the FastAPI server

This ensures your database is always up-to-date!

### Manual Migration in Docker

If you need to run migrations manually in a Docker container:

```bash
# Enter the running container
docker exec -it medicine-tracker-backend bash

# Run migrations
alembic upgrade head

# Exit the container
exit
```

## Example Workflow

### Scenario: Adding a new field to the Drug model

1. **Edit the model** (`backend/app/models.py`):
   ```python
   # Add new field
   instructions = Column(String, nullable=True)
   ```

2. **Create migration**:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add instructions field to Drug"
   ```

3. **Review the generated file** in `alembic/versions/`

4. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

5. **Done!** Your database now has the new field without losing any data.

## Backup and Restore

### Backup Database (Docker)

```bash
# Create backup of the Docker volume
docker run --rm -v medicine-data:/data -v $(pwd):/backup alpine tar czf /backup/medicine-db-backup.tar.gz -C /data .
```

### Restore Database (Docker)

```bash
# Restore from backup
docker run --rm -v medicine-data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/medicine-db-backup.tar.gz"
```

## Troubleshooting

### "Target database is not up to date"

This means there are pending migrations. Run:
```bash
alembic upgrade head
```

### "Can't locate revision identified by"

The migration history is out of sync. This can happen if you manually modified the database. Options:

1. **Reset migrations** (⚠️ LOSES DATA):
   ```bash
   rm backend/medicine.db
   alembic upgrade head
   ```

2. **Stamp current version** (if you know what you're doing):
   ```bash
   alembic stamp head
   ```

### Starting Fresh

If you want to completely reset the database:

```bash
# Local development
rm backend/medicine.db
alembic upgrade head

# Docker
docker-compose down -v  # -v removes volumes
docker-compose up --build
```

## Best Practices

1. ✅ **Always review** auto-generated migrations
2. ✅ **Test migrations** on a copy of production data before deploying
3. ✅ **Backup before** applying migrations in production
4. ✅ **Write descriptive** migration messages
5. ✅ **Commit migrations** to version control
6. ❌ **Never manually** edit the database schema
7. ❌ **Never delete** old migration files
