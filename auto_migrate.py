import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.types import Integer, String, Text, DateTime, Float, Boolean

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db

def map_sqlalchemy_type_to_sql(col_type, dialect_name):
    """
    Map SQLAlchemy column type to SQL type string.
    """
    if isinstance(col_type, String):
        return f"VARCHAR({col_type.length})" if col_type.length else "VARCHAR"
    elif isinstance(col_type, Text):
        return "TEXT"
    elif isinstance(col_type, Integer):
        return "INTEGER"
    elif isinstance(col_type, Float):
        return "DOUBLE PRECISION" if dialect_name == 'postgresql' else "REAL"
    elif isinstance(col_type, DateTime):
        return "TIMESTAMP" if dialect_name == 'postgresql' else "TIMESTAMP"
    elif isinstance(col_type, Boolean):
        return "BOOLEAN"
    else:
        return str(col_type)

def run_migration():
    app = create_app()
    with app.app_context():
        engine = db.engine
        dialect_name = engine.dialect.name
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"Connecting to database: {db_url} (Dialect: {dialect_name})")
        
        # 1. Create any missing tables (db.create_all() is safe and does not drop existing tables or delete rows)
        print("Ensuring all tables exist...")
        db.create_all()
        
        # 2. Inspect existing schema to find missing columns
        inspector = inspect(engine)
        db_tables = inspector.get_table_names()
        model_tables = db.metadata.tables
        
        migrated_count = 0
        
        for table_name, model_table in model_tables.items():
            if table_name not in db_tables:
                # Should have been created by db.create_all(), but double check
                print(f"Table '{table_name}' was missing and should be created.")
                continue
            
            # Table exists, inspect existing columns
            existing_cols = {c['name']: c for c in inspector.get_columns(table_name)}
            
            for col_name, model_col in model_table.columns.items():
                if col_name not in existing_cols:
                    print(f"Missing column detected: Table '{table_name}', Column '{col_name}' ({model_col.type})")
                    
                    # Construct ALTER TABLE statement
                    type_sql = map_sqlalchemy_type_to_sql(model_col.type, dialect_name)
                    
                    # Handle nullable / default constraints safely for migration
                    null_sql = "" if model_col.nullable else " DEFAULT ''"
                    if isinstance(model_col.type, Integer) and not model_col.nullable:
                        null_sql = " DEFAULT 0"
                    elif isinstance(model_col.type, Boolean) and not model_col.nullable:
                        null_sql = " DEFAULT FALSE"
                    
                    alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {type_sql}{null_sql}"
                    print(f"Executing: {alter_query}")
                    
                    try:
                        db.session.execute(text(alter_query))
                        db.session.commit()
                        print(f"Successfully added column '{col_name}' to table '{table_name}'.")
                        migrated_count += 1
                    except Exception as e:
                        db.session.rollback()
                        print(f"ERROR executing migration query: {e}")
        
        print("\n=== MIGRATION COMPLETE ===")
        if migrated_count > 0:
            print(f"Successfully added {migrated_count} column(s) to the database.")
        else:
            print("No missing columns were detected. Database matches models perfectly!")

if __name__ == '__main__':
    try:
        run_migration()
    except Exception as e:
        print(f"\nMigration failed to run: {e}")
        import traceback
        traceback.print_exc()
