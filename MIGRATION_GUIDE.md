# Database Migration Guide

## Migrating from "shares" to "stocks" Schema

If you have an existing database using the old schema (with `shares` table), you need to run the migration script before using the updated application.

### When Do You Need to Migrate?

You need to migrate if:
- You have an existing `instance/database.db` file
- Your database was created before this update
- You see errors about missing `stocks` table

### Migration Steps

#### 1. Backup Your Database (Recommended)

```bash
# Backup your existing database
cp instance/database.db instance/database.db.backup
```

#### 2. Run the Migration Script

```bash
python3 migrate_database.py
```

**Expected Output:**
```
Database Migration: shares → stocks
============================================================
🔄 Old schema detected. Starting migration...
============================================================
📝 Step 1/3: Renaming 'shares' table to 'stocks'...
   ✓ Table renamed
📝 Step 2/3: Updating company_info table...
   ✓ Column 'total_shares' renamed to 'total_stocks'
📝 Step 3/3: Verifying migration...
   ✓ Verified: X stock records
   ✓ Verified: 1 company info record(s)
============================================================
✅ Migration completed successfully!

Database schema updated:
  • shares → stocks
  • total_shares → total_stocks

⚠️  Note: Column 'share_count' in stocks table remains unchanged
   (SQLite doesn't support renaming columns directly in ALTER TABLE)
   The application code handles this mapping internally.
```

#### 3. Verify Migration

After running the migration, start your application:

```bash
python3 app.py
```

The application should start normally. If you see any errors, restore your backup:

```bash
cp instance/database.db.backup instance/database.db
```

### For New Installations

If you're setting up the application for the first time, you don't need to run the migration. The database will be created with the new schema automatically.

### What Gets Migrated?

| Old Name | New Name | Location |
|----------|----------|----------|
| `shares` (table) | `stocks` | Database |
| `total_shares` (column) | `total_stocks` | company_info table |

**Note:** The column `share_count` inside the `stocks` table keeps its name due to SQLite limitations. The application handles this internally.

### Rollback

If something goes wrong during migration:

1. The migration script uses transactions - if it fails, changes are rolled back automatically
2. If you need to restore from backup:
   ```bash
   cp instance/database.db.backup instance/database.db
   ```

### Migration Safety

The migration script is:
- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Transactional**: All-or-nothing approach
- ✅ **Non-destructive**: Creates new tables, doesn't delete data
- ✅ **Verified**: Checks data integrity before committing

### Support

If you encounter any issues during migration, please:
1. Check the error message carefully
2. Verify your backup is in place
3. Report the issue with the full error output
