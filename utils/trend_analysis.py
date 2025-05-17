"""
Asset Trend Analysis Utilities

This module provides functions for analyzing historical asset data,
calculating trends, and generating reports.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Union, Any

import pandas as pd
import numpy as np
from sqlalchemy import func

from app import db
from models.asset_history import AssetSnapshot, AssetTrend, FleetTrend
from models import Asset

logger = logging.getLogger(__name__)

def take_daily_snapshot(date_to_snapshot: date = None) -> bool:
    """
    Takes a daily snapshot of all assets for historical tracking.
    
    Args:
        date_to_snapshot: The date to take the snapshot for (defaults to today)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        snapshot_date = date_to_snapshot or date.today()
        logger.info(f"Taking daily snapshot for {snapshot_date}")
        
        # Get all active assets
        assets = Asset.query.filter_by(active=True).all()
        
        for asset in assets:
            # Check if snapshot already exists for this asset and date
            existing = AssetSnapshot.query.filter_by(
                asset_id=asset.id,
                snapshot_date=snapshot_date
            ).first()
            
            if existing:
                logger.debug(f"Snapshot already exists for asset {asset.id} on {snapshot_date}")
                continue
            
            # Create new snapshot with available data
            snapshot = AssetSnapshot(
                asset_id=asset.id,
                organization_id=asset.organization_id,
                snapshot_date=snapshot_date,
                latitude=asset.latitude,
                longitude=asset.longitude,
                location_name=asset.location_name,
                job_site_id=asset.job_site_id if hasattr(asset, 'job_site_id') else None,
                status=asset.status,
                engine_hours=asset.engine_hours if hasattr(asset, 'engine_hours') else None,
                fuel_level=asset.fuel_level if hasattr(asset, 'fuel_level') else None,
                maintenance_due=asset.maintenance_due if hasattr(asset, 'maintenance_due') else False,
                days_to_next_service=asset.days_to_next_service if hasattr(asset, 'days_to_next_service') else None,
            )
            
            # Add utilization hours and idle time from operational data if available
            # This would typically come from real-time tracking data
            # For now, we'll add placeholder calculations
            
            # Add financial data if available
            # This would typically come from financial systems
            
            db.session.add(snapshot)
        
        db.session.commit()
        logger.info(f"Successfully created snapshots for {len(assets)} assets")
        return True
        
    except Exception as e:
        logger.error(f"Error taking daily snapshot: {str(e)}")
        db.session.rollback()
        return False


def calculate_asset_trends(asset_id: int = None, 
                           period: str = 'DAILY',
                           start_date: date = None,
                           end_date: date = None) -> bool:
    """
    Calculate trends for a specific asset or all assets over a time period.
    
    Args:
        asset_id: Specific asset ID to calculate trends for, or None for all assets
        period: Trend period ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')
        start_date: Start date for trend calculation
        end_date: End date for trend calculation
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set default dates if not provided
        end_date = end_date or date.today()
        
        if period == 'DAILY':
            start_date = start_date or (end_date - timedelta(days=1))
        elif period == 'WEEKLY':
            start_date = start_date or (end_date - timedelta(days=7))
        elif period == 'MONTHLY':
            start_date = start_date or (end_date - timedelta(days=30))
        elif period == 'QUARTERLY':
            start_date = start_date or (end_date - timedelta(days=90))
        elif period == 'YEARLY':
            start_date = start_date or (end_date - timedelta(days=365))
        
        logger.info(f"Calculating {period} trends from {start_date} to {end_date}")
        
        # Query to get asset snapshots for the specified period
        query = AssetSnapshot.query.filter(
            AssetSnapshot.snapshot_date >= start_date,
            AssetSnapshot.snapshot_date <= end_date
        )
        
        if asset_id:
            query = query.filter(AssetSnapshot.asset_id == asset_id)
            assets = [Asset.query.get(asset_id)]
        else:
            # Get all assets with snapshots in the period
            asset_ids = db.session.query(AssetSnapshot.asset_id).distinct().filter(
                AssetSnapshot.snapshot_date >= start_date,
                AssetSnapshot.snapshot_date <= end_date
            ).all()
            asset_ids = [a[0] for a in asset_ids]
            assets = Asset.query.filter(Asset.id.in_(asset_ids)).all()
        
        trend_date = end_date
        
        for asset in assets:
            # Get snapshots for this asset
            asset_snapshots = query.filter(AssetSnapshot.asset_id == asset.id).order_by(
                AssetSnapshot.snapshot_date
            ).all()
            
            if not asset_snapshots:
                continue
                
            # Calculate trend metrics
            utilization_rate = calculate_utilization_rate(asset_snapshots)
            idle_percentage = calculate_idle_percentage(asset_snapshots)
            efficiency_score = calculate_efficiency_score(asset_snapshots)
            
            # Financial metrics
            cost_per_hour = calculate_cost_per_hour(asset_snapshots)
            revenue_per_hour = calculate_revenue_per_hour(asset_snapshots)
            profit_margin = calculate_profit_margin(cost_per_hour, revenue_per_hour)
            
            # Get previous period data for change calculation
            prev_start = start_date - (end_date - start_date)
            prev_end = start_date - timedelta(days=1)
            
            prev_trend = AssetTrend.query.filter_by(
                asset_id=asset.id,
                trend_period=period,
                trend_date=prev_end
            ).first()
            
            # Calculate changes from previous period
            utilization_change = None
            efficiency_change = None
            cost_change = None
            
            if prev_trend:
                if prev_trend.utilization_rate:
                    utilization_change = utilization_rate - prev_trend.utilization_rate
                if prev_trend.efficiency_score:
                    efficiency_change = efficiency_score - prev_trend.efficiency_score
                if prev_trend.cost_per_hour and cost_per_hour:
                    cost_change = ((cost_per_hour / prev_trend.cost_per_hour) - 1) * 100
            
            # Maintenance metrics
            maintenance_compliance = calculate_maintenance_compliance(asset_snapshots)
            downtime_hours = calculate_downtime_hours(asset_snapshots)
            
            # Update or create trend record
            trend = AssetTrend.query.filter_by(
                asset_id=asset.id,
                trend_date=trend_date,
                trend_period=period
            ).first()
            
            if trend:
                # Update existing trend
                trend.utilization_rate = utilization_rate
                trend.idle_percentage = idle_percentage
                trend.efficiency_score = efficiency_score
                trend.cost_per_hour = cost_per_hour
                trend.revenue_per_hour = revenue_per_hour
                trend.profit_margin = profit_margin
                trend.utilization_change = utilization_change
                trend.efficiency_change = efficiency_change
                trend.cost_change = cost_change
                trend.maintenance_compliance = maintenance_compliance
                trend.downtime_hours = downtime_hours
                trend.updated_at = datetime.utcnow()
            else:
                # Create new trend record
                trend = AssetTrend(
                    asset_id=asset.id,
                    organization_id=asset.organization_id,
                    trend_date=trend_date,
                    trend_period=period,
                    utilization_rate=utilization_rate,
                    idle_percentage=idle_percentage,
                    efficiency_score=efficiency_score,
                    cost_per_hour=cost_per_hour,
                    revenue_per_hour=revenue_per_hour,
                    profit_margin=profit_margin,
                    utilization_change=utilization_change,
                    efficiency_change=efficiency_change,
                    cost_change=cost_change,
                    maintenance_compliance=maintenance_compliance,
                    downtime_hours=downtime_hours
                )
                db.session.add(trend)
                
        db.session.commit()
        logger.info(f"Successfully calculated {period} trends for {len(assets)} assets")
        return True
        
    except Exception as e:
        logger.error(f"Error calculating asset trends: {str(e)}")
        db.session.rollback()
        return False


def calculate_fleet_trends(organization_id: int,
                           category: str = None,
                           period: str = 'DAILY',
                           trend_date: date = None) -> bool:
    """
    Calculate aggregate fleet trends for an organization.
    
    Args:
        organization_id: Organization ID
        category: Asset category to filter by, or None for all assets
        period: Trend period ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')
        trend_date: Date for the trend (defaults to today)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        trend_date = trend_date or date.today()
        logger.info(f"Calculating fleet trends for org {organization_id} on {trend_date}")
        
        # Calculate date ranges based on period
        if period == 'DAILY':
            start_date = trend_date - timedelta(days=1)
        elif period == 'WEEKLY':
            start_date = trend_date - timedelta(days=7)
        elif period == 'MONTHLY':
            start_date = trend_date - timedelta(days=30)
        elif period == 'QUARTERLY':
            start_date = trend_date - timedelta(days=90)
        elif period == 'YEARLY':
            start_date = trend_date - timedelta(days=365)
        else:
            raise ValueError(f"Invalid period: {period}")
            
        # Get asset trends for the period
        asset_trends_query = AssetTrend.query.filter(
            AssetTrend.organization_id == organization_id,
            AssetTrend.trend_date == trend_date,
            AssetTrend.trend_period == period
        )
        
        # Get asset query for counting
        assets_query = Asset.query.filter_by(organization_id=organization_id)
        
        if category:
            # Apply category filter if specified
            assets_query = assets_query.filter_by(category=category)
            asset_trends_query = asset_trends_query.join(Asset).filter(Asset.category == category)
        
        # Get counts and metrics
        total_assets = assets_query.count()
        active_assets = assets_query.filter_by(active=True).count()
        inactive_assets = total_assets - active_assets
        
        # Get assets with maintenance due
        maintenance_due_count = assets_query.filter_by(
            active=True,
            maintenance_due=True
        ).count()
        
        # Get asset trends and calculate averages
        asset_trends = asset_trends_query.all()
        
        if not asset_trends:
            logger.warning(f"No asset trends found for org {organization_id} on {trend_date}")
            return False
            
        # Calculate average metrics
        utilization_rates = [t.utilization_rate for t in asset_trends if t.utilization_rate is not None]
        idle_percentages = [t.idle_percentage for t in asset_trends if t.idle_percentage is not None]
        efficiency_scores = [t.efficiency_score for t in asset_trends if t.efficiency_score is not None]
        costs_per_hour = [t.cost_per_hour for t in asset_trends if t.cost_per_hour is not None]
        revenues_per_hour = [t.revenue_per_hour for t in asset_trends if t.revenue_per_hour is not None]
        profit_margins = [t.profit_margin for t in asset_trends if t.profit_margin is not None]
        
        average_utilization = sum(utilization_rates) / len(utilization_rates) if utilization_rates else None
        average_idle_time = sum(idle_percentages) / len(idle_percentages) if idle_percentages else None
        average_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else None
        
        # Financial calculations
        total_cost = sum(c for t in asset_trends for c in [t.cost_per_hour] if c is not None)
        total_revenue = sum(r for t in asset_trends for r in [t.revenue_per_hour] if r is not None)
        average_profit_margin = sum(profit_margins) / len(profit_margins) if profit_margins else None
        
        # Calculate cost per operating hour
        total_operating_hours = sum(t.utilization_rate * 24 for t in asset_trends if t.utilization_rate is not None)
        cost_per_operating_hour = total_cost / total_operating_hours if total_operating_hours else None
        
        # Get previous period data for change calculation
        prev_date = start_date - timedelta(days=1)
        prev_trend = FleetTrend.query.filter_by(
            organization_id=organization_id,
            category=category,
            trend_period=period,
            trend_date=prev_date
        ).first()
        
        # Calculate changes from previous period
        utilization_change = None
        cost_change = None
        efficiency_change = None
        
        if prev_trend:
            if prev_trend.average_utilization and average_utilization:
                utilization_change = average_utilization - prev_trend.average_utilization
            
            if prev_trend.total_cost and total_cost:
                cost_change = ((total_cost / prev_trend.total_cost) - 1) * 100
                
            if prev_trend.average_efficiency and average_efficiency:
                efficiency_change = average_efficiency - prev_trend.average_efficiency
        
        # Get job site count
        job_site_count = db.session.query(
            func.count(func.distinct(AssetSnapshot.job_site_id))
        ).filter(
            AssetSnapshot.organization_id == organization_id,
            AssetSnapshot.snapshot_date >= start_date,
            AssetSnapshot.snapshot_date <= trend_date,
            AssetSnapshot.job_site_id.isnot(None)
        ).scalar()
        
        # Update or create fleet trend record
        fleet_trend = FleetTrend.query.filter_by(
            organization_id=organization_id,
            category=category,
            trend_date=trend_date,
            trend_period=period
        ).first()
        
        if fleet_trend:
            # Update existing trend
            fleet_trend.total_assets = total_assets
            fleet_trend.active_assets = active_assets
            fleet_trend.inactive_assets = inactive_assets
            fleet_trend.maintenance_due_count = maintenance_due_count
            fleet_trend.average_utilization = average_utilization
            fleet_trend.average_idle_time = average_idle_time
            fleet_trend.average_efficiency = average_efficiency
            fleet_trend.total_cost = total_cost
            fleet_trend.total_revenue = total_revenue
            fleet_trend.average_profit_margin = average_profit_margin
            fleet_trend.cost_per_operating_hour = cost_per_operating_hour
            fleet_trend.utilization_change = utilization_change
            fleet_trend.cost_change = cost_change
            fleet_trend.efficiency_change = efficiency_change
            fleet_trend.job_site_count = job_site_count
            fleet_trend.updated_at = datetime.utcnow()
        else:
            # Create new fleet trend
            fleet_trend = FleetTrend(
                organization_id=organization_id,
                category=category,
                trend_date=trend_date,
                trend_period=period,
                total_assets=total_assets,
                active_assets=active_assets,
                inactive_assets=inactive_assets,
                maintenance_due_count=maintenance_due_count,
                average_utilization=average_utilization,
                average_idle_time=average_idle_time,
                average_efficiency=average_efficiency,
                total_cost=total_cost,
                total_revenue=total_revenue,
                average_profit_margin=average_profit_margin,
                cost_per_operating_hour=cost_per_operating_hour,
                utilization_change=utilization_change,
                cost_change=cost_change,
                efficiency_change=efficiency_change,
                job_site_count=job_site_count
            )
            db.session.add(fleet_trend)
            
        db.session.commit()
        logger.info(f"Successfully calculated fleet trends for org {organization_id}")
        return True
            
    except Exception as e:
        logger.error(f"Error calculating fleet trends: {str(e)}")
        db.session.rollback()
        return False


def get_asset_trend_data(asset_id: int, 
                         period: str = 'DAILY',
                         days: int = 30) -> Dict:
    """
    Get trend data for a specific asset over time.
    
    Args:
        asset_id: Asset ID to get trends for
        period: Trend period ('DAILY', 'WEEKLY', 'MONTHLY')
        days: Number of days of data to include
        
    Returns:
        dict: Dictionary of trend data for charts
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get the asset
        asset = Asset.query.get(asset_id)
        if not asset:
            return {'error': 'Asset not found'}
            
        # Get trend data for the period
        trends = AssetTrend.query.filter(
            AssetTrend.asset_id == asset_id,
            AssetTrend.trend_period == period,
            AssetTrend.trend_date >= start_date,
            AssetTrend.trend_date <= end_date
        ).order_by(AssetTrend.trend_date).all()
        
        if not trends:
            return {
                'asset': {
                    'id': asset_id,
                    'name': asset.name,
                    'category': asset.category
                },
                'dates': [],
                'utilization': [],
                'efficiency': [],
                'cost': [],
                'revenue': [],
                'profit_margin': [],
                'maintenance_compliance': []
            }
            
        # Format data for charts
        dates = [t.trend_date.strftime('%Y-%m-%d') for t in trends]
        utilization = [float(t.utilization_rate) if t.utilization_rate is not None else None for t in trends]
        efficiency = [float(t.efficiency_score) if t.efficiency_score is not None else None for t in trends]
        cost = [float(t.cost_per_hour) if t.cost_per_hour is not None else None for t in trends]
        revenue = [float(t.revenue_per_hour) if t.revenue_per_hour is not None else None for t in trends]
        profit_margin = [float(t.profit_margin) if t.profit_margin is not None else None for t in trends]
        maintenance = [float(t.maintenance_compliance) if t.maintenance_compliance is not None else None for t in trends]
        
        return {
            'asset': {
                'id': asset_id,
                'name': asset.name,
                'category': asset.category
            },
            'dates': dates,
            'utilization': utilization,
            'efficiency': efficiency,
            'cost': cost,
            'revenue': revenue,
            'profit_margin': profit_margin,
            'maintenance_compliance': maintenance
        }
        
    except Exception as e:
        logger.error(f"Error getting asset trend data: {str(e)}")
        return {'error': str(e)}


def get_fleet_trend_data(organization_id: int,
                         category: str = None,
                         period: str = 'DAILY',
                         days: int = 30) -> Dict:
    """
    Get trend data for a fleet or category over time.
    
    Args:
        organization_id: Organization ID
        category: Asset category or None for all
        period: Trend period ('DAILY', 'WEEKLY', 'MONTHLY')
        days: Number of days of data to include
        
    Returns:
        dict: Dictionary of trend data for charts
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get trend data for the fleet
        trends = FleetTrend.query.filter(
            FleetTrend.organization_id == organization_id,
            FleetTrend.trend_period == period,
            FleetTrend.trend_date >= start_date,
            FleetTrend.trend_date <= end_date
        )
        
        if category:
            trends = trends.filter(FleetTrend.category == category)
            
        trends = trends.order_by(FleetTrend.trend_date).all()
        
        if not trends:
            return {
                'fleet': {
                    'organization_id': organization_id,
                    'category': category
                },
                'dates': [],
                'utilization': [],
                'efficiency': [],
                'cost': [],
                'revenue': [],
                'profit_margin': [],
                'active_assets': []
            }
            
        # Format data for charts
        dates = [t.trend_date.strftime('%Y-%m-%d') for t in trends]
        utilization = [float(t.average_utilization) if t.average_utilization is not None else None for t in trends]
        efficiency = [float(t.average_efficiency) if t.average_efficiency is not None else None for t in trends]
        cost = [float(t.total_cost) if t.total_cost is not None else None for t in trends]
        revenue = [float(t.total_revenue) if t.total_revenue is not None else None for t in trends]
        profit_margin = [float(t.average_profit_margin) if t.average_profit_margin is not None else None for t in trends]
        active_assets = [int(t.active_assets) if t.active_assets is not None else None for t in trends]
        
        return {
            'fleet': {
                'organization_id': organization_id,
                'category': category
            },
            'dates': dates,
            'utilization': utilization,
            'efficiency': efficiency,
            'cost': cost,
            'revenue': revenue,
            'profit_margin': profit_margin,
            'active_assets': active_assets
        }
        
    except Exception as e:
        logger.error(f"Error getting fleet trend data: {str(e)}")
        return {'error': str(e)}


# Helper functions for trend calculations

def calculate_utilization_rate(snapshots: List[AssetSnapshot]) -> float:
    """Calculate the utilization rate from snapshots (0-100%)"""
    if not snapshots:
        return None
        
    # For now, implement a simplified calculation
    # In a real system, this would use actual utilization hours
    total_hours = sum(s.utilization_hours or 0 for s in snapshots)
    available_hours = len(snapshots) * 24  # 24 hours per day
    
    if available_hours == 0:
        return 0
        
    return (total_hours / available_hours) * 100


def calculate_idle_percentage(snapshots: List[AssetSnapshot]) -> float:
    """Calculate the idle percentage from snapshots (0-100%)"""
    if not snapshots:
        return None
        
    # Implement a simplified calculation
    total_utilization = sum(s.utilization_hours or 0 for s in snapshots)
    total_idle = sum(s.idle_time or 0 for s in snapshots)
    
    if total_utilization + total_idle == 0:
        return 0
        
    return (total_idle / (total_utilization + total_idle)) * 100


def calculate_efficiency_score(snapshots: List[AssetSnapshot]) -> float:
    """Calculate an efficiency score (0-100) based on utilization and idle time"""
    if not snapshots:
        return None
        
    utilization_rate = calculate_utilization_rate(snapshots)
    idle_percentage = calculate_idle_percentage(snapshots)
    
    if utilization_rate is None or idle_percentage is None:
        return None
        
    # Simple weighted formula: 
    # 70% weight to utilization, 30% weight to non-idle time
    return (0.7 * utilization_rate) + (0.3 * (100 - idle_percentage))


def calculate_cost_per_hour(snapshots: List[AssetSnapshot]) -> float:
    """Calculate cost per hour from snapshots"""
    if not snapshots:
        return None
        
    total_cost = sum(s.daily_cost or 0 for s in snapshots)
    total_hours = sum(s.utilization_hours or 0 for s in snapshots)
    
    if total_hours == 0:
        return 0
        
    return total_cost / total_hours


def calculate_revenue_per_hour(snapshots: List[AssetSnapshot]) -> float:
    """Calculate revenue per hour from snapshots"""
    if not snapshots:
        return None
        
    total_revenue = sum(s.revenue_generated or 0 for s in snapshots)
    total_hours = sum(s.utilization_hours or 0 for s in snapshots)
    
    if total_hours == 0:
        return 0
        
    return total_revenue / total_hours


def calculate_profit_margin(cost_per_hour: float, revenue_per_hour: float) -> float:
    """Calculate profit margin percentage"""
    if cost_per_hour is None or revenue_per_hour is None:
        return None
        
    if revenue_per_hour == 0:
        return 0
        
    return ((revenue_per_hour - cost_per_hour) / revenue_per_hour) * 100


def calculate_maintenance_compliance(snapshots: List[AssetSnapshot]) -> float:
    """Calculate maintenance compliance percentage"""
    # This is a simplified implementation
    # In a real system, this would check scheduled vs. completed maintenance
    if not snapshots:
        return None
        
    maintenance_due_count = sum(1 for s in snapshots if s.maintenance_due)
    
    if len(snapshots) == 0:
        return 100
        
    return 100 - ((maintenance_due_count / len(snapshots)) * 100)


def calculate_downtime_hours(snapshots: List[AssetSnapshot]) -> float:
    """Calculate downtime hours"""
    # This is a simplified implementation
    # In a real system, this would use actual downtime records
    if not snapshots:
        return None
        
    # Count snapshots with status indicating downtime
    downtime_snapshots = sum(1 for s in snapshots if s.status == 'maintenance' or s.status == 'repair')
    
    # Estimate 24 hours per day of downtime
    return downtime_snapshots * 24