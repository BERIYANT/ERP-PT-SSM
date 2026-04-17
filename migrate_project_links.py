from sqlalchemy import text, inspect
from app import create_app
from models import db

app = create_app('development')


def ensure_column(table_name, column_name, ddl):
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    if column_name in columns:
        print(f"ℹ️  {table_name}.{column_name} sudah ada")
        return
    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))
    db.session.commit()
    print(f"✅ Menambahkan kolom {table_name}.{column_name}")


def ensure_fk(table_name, fk_name, statement):
    result = db.session.execute(text(f"SHOW CREATE TABLE {table_name}"))
    create_sql = result.fetchone()[1]
    if fk_name in create_sql:
        print(f"ℹ️  FK {fk_name} sudah ada")
        return
    db.session.execute(text(statement))
    db.session.commit()
    print(f"✅ Menambahkan FK {fk_name}")


def ensure_index(table_name, index_name, statement):
    inspector = inspect(db.engine)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    if index_name in indexes:
        print(f"ℹ️  Index {index_name} sudah ada")
        return
    db.session.execute(text(statement))
    db.session.commit()
    print(f"✅ Menambahkan index {index_name}")


if __name__ == '__main__':
    with app.app_context():
        ensure_column('materials', 'project_id', 'project_id INT NULL')
        ensure_column('petty_cash', 'project_id', 'project_id INT NULL')

        ensure_fk(
            'materials',
            'fk_materials_project',
            'ALTER TABLE materials ADD CONSTRAINT fk_materials_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL'
        )
        ensure_fk(
            'petty_cash',
            'fk_petty_cash_project',
            'ALTER TABLE petty_cash ADD CONSTRAINT fk_petty_cash_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL'
        )

        ensure_index('materials', 'idx_materials_project_id', 'CREATE INDEX idx_materials_project_id ON materials(project_id)')
        ensure_index('petty_cash', 'idx_petty_cash_project_id', 'CREATE INDEX idx_petty_cash_project_id ON petty_cash(project_id)')
        print('✅ Migrasi relasi project untuk material & petty cash selesai')
