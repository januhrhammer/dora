"""
Data migration script to transfer data from medicinebu.db to medicine.db

This script safely transfers all drug data from the old database to the new one,
handling schema differences.
"""

import sqlite3
from datetime import datetime

def migrate_data():
    """Transfer data from medicinebu.db to medicine.db"""

    # Connect to both databases
    old_db = sqlite3.connect('medicinebu.db')
    new_db = sqlite3.connect('medicine.db')

    old_cursor = old_db.cursor()
    new_cursor = new_db.cursor()

    try:
        # First, let's see what columns exist in the old database
        old_cursor.execute("PRAGMA table_info(drugs)")
        old_columns = [col[1] for col in old_cursor.fetchall()]
        print(f"Old database columns: {old_columns}")

        # Get all data from old database
        old_cursor.execute("SELECT * FROM drugs")
        old_data = old_cursor.fetchall()

        print(f"\nFound {len(old_data)} drugs in old database")

        if len(old_data) == 0:
            print("No data to migrate!")
            return

        # Get column indices from old database
        old_cursor.execute("SELECT * FROM drugs LIMIT 0")
        old_col_names = [desc[0] for desc in old_cursor.description]

        # Create a mapping of column name to index
        col_map = {name: idx for idx, name in enumerate(old_col_names)}

        # Migrate each drug
        migrated = 0
        for row in old_data:
            # Extract data with defaults for missing fields
            drug_data = {
                'name': row[col_map['name']],
                'dosage_strength': row[col_map.get('dosage_strength')] if 'dosage_strength' in col_map else None,
                'package_size': row[col_map['package_size']],
                'schedule_type': row[col_map.get('schedule_type')] if 'schedule_type' in col_map else 'daily',
                'morning_pre_food': row[col_map.get('morning_pre_food', col_map.get('pills_per_dose', 0))],
                'morning_post_food': row[col_map.get('morning_post_food', 0)],
                'evening_pre_food': row[col_map.get('evening_pre_food', 0)],
                'evening_post_food': row[col_map.get('evening_post_food', 0)],
                'even_week_pills': row[col_map.get('even_week_pills')] if 'even_week_pills' in col_map else None,
                'odd_week_pills': row[col_map.get('odd_week_pills')] if 'odd_week_pills' in col_map else None,
                'current_amount': row[col_map['current_amount']],
                'notes': row[col_map.get('notes')] if 'notes' in col_map else None,
                'last_refilled_at': None,  # New field, set to None for old data
                'created_at': row[col_map.get('created_at')] if 'created_at' in col_map else datetime.utcnow().isoformat(),
                'updated_at': row[col_map.get('updated_at')] if 'updated_at' in col_map else datetime.utcnow().isoformat(),
            }

            # Insert into new database
            new_cursor.execute("""
                INSERT INTO drugs (
                    name, dosage_strength, package_size, schedule_type,
                    morning_pre_food, morning_post_food, evening_pre_food, evening_post_food,
                    even_week_pills, odd_week_pills, current_amount, notes,
                    last_refilled_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug_data['name'],
                drug_data['dosage_strength'],
                drug_data['package_size'],
                drug_data['schedule_type'],
                drug_data['morning_pre_food'],
                drug_data['morning_post_food'],
                drug_data['evening_pre_food'],
                drug_data['evening_post_food'],
                drug_data['even_week_pills'],
                drug_data['odd_week_pills'],
                drug_data['current_amount'],
                drug_data['notes'],
                drug_data['last_refilled_at'],
                drug_data['created_at'],
                drug_data['updated_at']
            ))

            migrated += 1
            print(f"[OK] Migrated: {drug_data['name']}")

        # Commit changes
        new_db.commit()

        print(f"\n[SUCCESS] Successfully migrated {migrated} drugs!")

        # Verify migration
        new_cursor.execute("SELECT COUNT(*) FROM drugs")
        new_count = new_cursor.fetchone()[0]
        print(f"New database now has {new_count} drugs")

    except Exception as e:
        print(f"[ERROR] Error during migration: {e}")
        new_db.rollback()
        raise

    finally:
        old_db.close()
        new_db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Medicine Database Migration Tool")
    print("=" * 60)
    print("\nThis will transfer data from medicinebu.db to medicine.db")
    print("\nStarting migration...\n")

    migrate_data()

    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
