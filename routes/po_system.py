"""
Purchase Order System Routes
Complete PO management with approval workflows
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

po_bp = Blueprint('po_system', __name__)

@po_bp.route('/po-system')
def po_dashboard():
    """PO system dashboard with active orders"""
    try:
        from services.execute_sql_direct import execute_sql_query
        
        # Get PO summary data
        pos = execute_sql_query("""
            SELECT po.*, 
                   COUNT(li.id) as line_item_count,
                   COALESCE(SUM(li.total_price), 0) as calculated_total
            FROM public.purchase_orders po
            LEFT JOIN public.po_line_items li ON po.id = li.po_id
            GROUP BY po.id
            ORDER BY po.created_at DESC
        """)
        
        # Get status breakdown
        status_summary = execute_sql_query("""
            SELECT status, COUNT(*) as count, SUM(total_amount) as total_value
            FROM public.purchase_orders
            GROUP BY status
        """)
        
        return render_template('po_system/dashboard.html', 
                             purchase_orders=pos,
                             status_summary=status_summary)
    except Exception as e:
        logger.error(f"PO dashboard error: {e}")
        return render_template('po_system/dashboard.html', 
                             purchase_orders=[],
                             status_summary=[])

@po_bp.route('/po-system/create', methods=['GET', 'POST'])
def create_po():
    """Create new purchase order"""
    if request.method == 'POST':
        try:
            from services.execute_sql_direct import execute_sql_query
            
            data = request.get_json()
            
            # Insert PO header
            po_result = execute_sql_query(f"""
                INSERT INTO public.purchase_orders 
                (po_number, vendor_name, vendor_contact, total_amount, status, requested_by, delivery_date)
                VALUES ('{data['po_number']}', '{data['vendor_name']}', 
                        '{data.get('vendor_contact', '')}', {data['total_amount']}, 
                        'draft', '{data.get('requested_by', 'System')}', 
                        '{data.get('delivery_date', '')}')
                RETURNING id
            """)
            
            if po_result:
                po_id = po_result[0]['id']
                
                # Insert line items
                for item in data.get('line_items', []):
                    execute_sql_query(f"""
                        INSERT INTO public.po_line_items 
                        (po_id, item_description, quantity, unit_price, total_price, 
                         asset_category, cost_code, job_number)
                        VALUES ({po_id}, '{item['description']}', {item['quantity']},
                                {item['unit_price']}, {item['total_price']}, 
                                '{item.get('category', '')}', '{item.get('cost_code', '')}',
                                '{item.get('job_number', '')}')
                    """)
                
                return jsonify({'success': True, 'po_id': po_id})
            
            return jsonify({'success': False, 'error': 'Failed to create PO'})
            
        except Exception as e:
            logger.error(f"PO creation error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    return render_template('po_system/create.html')

@po_bp.route('/po-system/<int:po_id>')
def view_po(po_id):
    """View specific purchase order"""
    try:
        from services.execute_sql_direct import execute_sql_query
        
        # Get PO details
        po_data = execute_sql_query(f"""
            SELECT * FROM public.purchase_orders WHERE id = {po_id}
        """)
        
        if not po_data:
            flash('Purchase order not found', 'error')
            return redirect(url_for('po_system.po_dashboard'))
        
        # Get line items
        line_items = execute_sql_query(f"""
            SELECT * FROM public.po_line_items WHERE po_id = {po_id}
            ORDER BY id
        """)
        
        return render_template('po_system/view.html', 
                             po=po_data[0],
                             line_items=line_items)
    except Exception as e:
        logger.error(f"PO view error: {e}")
        flash('Error loading purchase order', 'error')
        return redirect(url_for('po_system.po_dashboard'))

@po_bp.route('/po-system/<int:po_id>/approve', methods=['POST'])
def approve_po(po_id):
    """Approve purchase order"""
    try:
        from services.execute_sql_direct import execute_sql_query
        
        data = request.get_json()
        approver = data.get('approved_by', 'System')
        
        execute_sql_query(f"""
            UPDATE public.purchase_orders 
            SET approval_status = 'approved',
                status = 'approved',
                approved_by = '{approver}',
                updated_at = NOW()
            WHERE id = {po_id}
        """)
        
        return jsonify({'success': True, 'message': 'PO approved successfully'})
        
    except Exception as e:
        logger.error(f"PO approval error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@po_bp.route('/api/po-metrics')
def po_metrics():
    """API endpoint for PO system metrics"""
    try:
        from services.execute_sql_direct import execute_sql_query
        
        # Calculate key metrics
        total_pos = execute_sql_query("SELECT COUNT(*) as count FROM public.purchase_orders")[0]['count']
        
        pending_approval = execute_sql_query("""
            SELECT COUNT(*) as count FROM public.purchase_orders 
            WHERE approval_status = 'pending_approval'
        """)[0]['count']
        
        total_value = execute_sql_query("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM public.purchase_orders
        """)[0]['total']
        
        ytd_spending = execute_sql_query("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM public.purchase_orders 
            WHERE status = 'approved' AND EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE)
        """)[0]['total']
        
        return jsonify({
            'total_pos': total_pos,
            'pending_approval': pending_approval,
            'total_value': float(total_value),
            'ytd_spending': float(ytd_spending),
            'budget_utilization': (float(ytd_spending) / 500000.0) * 100  # Against $500k budget
        })
        
    except Exception as e:
        logger.error(f"PO metrics error: {e}")
        return jsonify({
            'total_pos': 0,
            'pending_approval': 0,
            'total_value': 0,
            'ytd_spending': 0,
            'budget_utilization': 0
        })