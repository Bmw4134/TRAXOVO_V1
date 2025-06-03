"""
Command-line interface utilities for the application.
"""
import click
import os
from datetime import datetime
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
# Import db directly from models to avoid circular imports
from models import db, User, Asset, AssetHistory, MaintenanceRecord, APIConfig


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database and create tables."""
    click.echo('Initializing database...')
    db.create_all()
    click.echo('Database initialized successfully.')


@click.command('create-admin')
@click.option('--username', prompt=True)
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin_command(username, email, password):
    """Create an admin user."""
    user = User.query.filter_by(username=username).first()
    if user:
        click.echo(f'Error: User {username} already exists.')
        return

    user = User(
        username=username,
        email=email,
        is_admin=True,
        created_at=datetime.utcnow()
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'Admin user {username} created successfully.')


@click.command('import-assets')
@click.option('--file-path', default='data/processed_data.json', help='Path to the asset data JSON file')
@with_appcontext
def import_assets_command(file_path):
    """Import assets from JSON file into the database."""
    import json
    from app import logger
    
    if not os.path.exists(file_path):
        click.echo(f'Error: File {file_path} not found.')
        return
    
    try:
        with open(file_path, 'r') as f:
            assets_data = json.load(f)
        
        click.echo(f'Processing {len(assets_data)} assets...')
        count = 0
        
        for data in assets_data:
            asset = Asset.from_json(data)
            db.session.add(asset)
            count += 1
            
            # Commit in batches to avoid memory issues
            if count % 100 == 0:
                db.session.commit()
                click.echo(f'Processed {count} assets...')
        
        # Commit any remaining assets
        db.session.commit()
        click.echo(f'Successfully imported {count} assets into the database.')
    
    except Exception as e:
        logger.error(f'Error importing assets: {e}')
        click.echo(f'Error importing assets: {e}')


def register_cli_commands(app):
    """Register CLI commands with the application."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(import_assets_command)