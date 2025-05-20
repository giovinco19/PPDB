from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import app, db
from datetime import datetime

def upgrade():
    # Add the created_at column to the pendaftaran table
    db.engine.execute('ALTER TABLE pendaftaran ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
    
    # Update existing rows to have a created_at value
    db.engine.execute('UPDATE pendaftaran SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL')

def downgrade():
    # Remove the created_at column if needed
    db.engine.execute('ALTER TABLE pendaftaran DROP COLUMN created_at')
