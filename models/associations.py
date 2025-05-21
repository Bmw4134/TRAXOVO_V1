"""
Association tables for many-to-many relationships.
"""
from sqlalchemy import Table, Column, Integer, ForeignKey
from app import db

# Association table between assets and job sites
asset_jobsite_association = Table(
    'asset_jobsite_association',
    db.Model.metadata,
    Column('asset_id', Integer, ForeignKey('assets.id')),
    Column('job_site_id', Integer, ForeignKey('job_sites.id'))
)