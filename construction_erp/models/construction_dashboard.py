from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime

class ConstructionDashboard(models.Model):
    _name = 'construction.dashboard.backend'
    _description = 'Python API Bridge for Javascript Dashboards'

    @api.model
    def get_construction_statistics(self):
        """ Native Python execution loop sweeping live project parameters logically """
        
        # 0. Construction Filter Context
        construction_projects = self.env['project.project'].search([('project_type', '=', 'construction')])
        project_ids = construction_projects.ids
        
        # 1. Total Metrics
        project_count = len(project_ids)
        estimate_count = self.env['construction.estimate'].search_count([('project_id', 'in', project_ids)])
        requisition_count = self.env['construction.material.requisition'].search_count([('project_id', 'in', project_ids)])
        scrap_count = self.env['construction.scrap'].search_count([('project_id', 'in', project_ids)])
        compliance_count = self.env['construction.compliance'].search_count([('project_id', 'in', project_ids)])
        material_count = self.env['product.template'].search_count([('is_construction_material', '=', True)])
        
        task_count = self.env['project.task'].search_count([('project_id', 'in', project_ids)])
        contractor_count = self.env['res.partner'].search_count([('is_contractor', '=', True)])
        
        # New Field Operations Metrics
        job_order_count = self.env['construction.job.order'].search_count([('project_id', 'in', project_ids)])
        material_request_count = self.env['construction.material.requisition'].search_count([('project_id', 'in', project_ids)])

        bill_count = self.env['account.move'].search_count([
            ('move_type', '=', 'in_invoice'),
            ('job_order_id.project_id', 'in', project_ids)
        ])
        construction_warehouses = construction_projects.mapped('warehouse_id').ids
        picking_count = self.env['stock.picking'].search_count([
            '|',
            ('location_id.warehouse_id', 'in', construction_warehouses),
            ('location_dest_id.warehouse_id', 'in', construction_warehouses)
        ])
        internal_picking_count = self.env['stock.picking'].search_count([
            ('picking_type_id.code', '=', 'internal'),
            '|',
            ('location_id.warehouse_id', 'in', construction_warehouses),
            ('location_dest_id.warehouse_id', 'in', construction_warehouses)
        ])
        inspection_count = self.env['construction.inspection'].search_count([('project_id', 'in', project_ids)])
        
        # Real Estate Metrics from pooled totals - Added strict company isolation
        units = self.env['real_estate.unit'].search([
            ('project_id', 'in', project_ids),
            ('currency_id', '=', self.env.company.currency_id.id)
        ])
        unit_count = sum(units.mapped('total_quantity'))
        sold_units = sum(units.mapped('quantity_sold'))
        reserved_units = sum(units.mapped('quantity_reserved'))
        available_units = sum(units.mapped('quantity_available'))
        
        # Valuation Logic Refined: Realized Revenue vs Potential Value
        realized_asset_value = sum(u.price * u.quantity_sold for u in units)
        potential_asset_value = sum(u.price * u.total_quantity for u in units)

        # 1.1 Multi-Project Sold Unit Analysis (Last 12 Months)
        sales_labels = []
        project_datasets = []
        today = fields.Date.context_today(self)
        
        # Build month labels once
        for i in range(11, -1, -1):
            label_date = today - relativedelta(months=i, day=1)
            sales_labels.append(label_date.strftime('%b %y'))

        # Aggregate for each project
        for proj in construction_projects:
            project_sales = []
            for i in range(11, -1, -1):
                start_date = today - relativedelta(months=i, day=1)
                end_date = today - relativedelta(months=i-1, day=1) if i > 0 else today + relativedelta(days=1)
                
                monthly_sales = self.env['sale.order'].search_count([
                    ('state', 'in', ['sale', 'done']),
                    ('project_id', '=', proj.id),
                    ('unit_id', '!=', False),
                    ('date_order', '>=', start_date),
                    ('date_order', '<', end_date)
                ])
                # We can return amount_total sum instead of count for more expression
                sales_query = self.env['sale.order'].search([
                    ('state', 'in', ['sale', 'done']),
                    ('project_id', '=', proj.id),
                    ('unit_id', '!=', False),
                    ('date_order', '>=', start_date),
                    ('date_order', '<', end_date)
                ])
                project_sales.append(sum(sales_query.mapped('amount_total')))
            
            # Only add to chart if there's any sales activity in the last 12 months for this project
            if sum(project_sales) > 0:
                project_datasets.append({
                    'label': proj.name,
                    'data': project_sales
                })

        # 2. Chart Arrays - Active Projects Array Mapped by Phase
        phases = self.env['construction.phase'].search([('active', '=', True)], order='sequence asc')
        phase_labels = []
        phase_data = []
        for p in phases:
            count = self.env['project.project'].search_count([
                ('current_phase_id', '=', p.id),
                ('project_type', '=', 'construction')
            ])
            phase_labels.append(p.name)
            phase_data.append(count)

        # 3. Chart Arrays - Commercial Sales Breakdown
        commercial_labels = ['Sold & Closed', 'Reserved / Pending', 'Available Inventory']
        commercial_data = [sold_units, reserved_units, available_units]

        # 4. Total Financial Tracking
        all_projects = self.env['project.project'].search([])
        total_revenue = 0.0
        total_costs = 0.0
        for proj in construction_projects:
            total_costs += proj.total_expense
            total_revenue += proj.total_collected

        # 5. Specialized Operational State Pulse
        job_orders = self.env['construction.job.order'].search([('project_id', 'in', project_ids)])
        contractor_pulse = {
            'offered': len(job_orders.filtered(lambda j: j.state == 'offered')),
            'active': len(job_orders.filtered(lambda j: j.state == 'active')),
            'inspection': len(job_orders.filtered(lambda j: j.state == 'ready_for_inspection')),
            'rework': len(job_orders.filtered(lambda j: j.state == 'rework')),
        }

        # 6. Proactive Procurement Risk Radar
        # Find materials where date needed is within 30 days and no PO exists
        # Simplified for dashboard dashboard: top 5 high lead-time materials missing POs
        risks = []
        mat_lines = self.env['construction.cost.material.line'].search([
            ('cost_sheet_id.project_id', 'in', project_ids),
            ('product_id.purchase_ok', '=', True)
        ])
        for line in mat_lines:
             po_lines = self.env['purchase.order.line'].search_count([
                 ('product_id', '=', line.product_id.id),
                 ('order_id.project_id', '=', line.cost_sheet_id.project_id.id)
             ])
             if po_lines == 0:
                 risks.append({
                     'id': line.id,
                     'material': line.product_id.display_name,
                     'project': line.cost_sheet_id.project_id.name,
                     'phase': line.phase_id.name or 'General',
                     'severity': 'high' if (line.product_id.produce_delay or 0) > 10 else 'medium'
                 })
        risks = risks[:5]

        # 6.1 Specialized Procurement Analyse Aggregation
        all_pos = self.env['purchase.order'].search([
            ('project_id', 'in', project_ids),
            ('state', '!=', 'cancel')
        ])
        procurement_analysis = {
            'total_value': sum(all_pos.mapped('amount_total')),
            'draft_count': len(all_pos.filtered(lambda p: p.state in ['draft', 'sent', 'to_approve'])),
            'confirmed_count': len(all_pos.filtered(lambda p: p.state in ['purchase', 'done'])),
        }

        # 7. Category Burn Data (Budget vs Actual)
        categories = ['Material', 'Labor', 'Equipment', 'Vehicle', 'Overhead']
        cost_sheets = self.env['construction.cost.sheet'].search([('project_id', 'in', project_ids)])
        burn_data = {
            'budget': [
                sum(cost_sheets.mapped('material_budget_total')),
                sum(cost_sheets.mapped('labor_budget_total')),
                sum(cost_sheets.mapped('equipment_budget_total')),
                sum(cost_sheets.mapped('vehicle_budget_total')),
                sum(cost_sheets.mapped('overhead_budget_total')),
            ],
            'actual': [
                sum(cost_sheets.material_line_ids.mapped('actual_amount_spent')),
                sum(cost_sheets.labor_line_ids.mapped('actual_amount_spent')),
                sum(cost_sheets.equipment_line_ids.mapped('actual_amount_spent')),
                sum(cost_sheets.vehicle_line_ids.mapped('actual_amount_spent')),
                sum(cost_sheets.overhead_line_ids.mapped('actual_amount_spent')),
            ]
        }

        # 8. Live Progress Feed
        recent_photos = self.env['construction.project.image'].search([('project_id', 'in', project_ids)], order='date desc, id desc', limit=8)
        recent_visuals = []
        for photo in recent_photos:
            recent_visuals.append({
                'id': photo.id,
                'name': photo.name or 'Site Update',
                'project': photo.project_id.name,
                'date': str(photo.date) if photo.date else ''
            })

        # 9. Actionable Lists
        pending_inspections = self.env['construction.inspection'].search([('state', '=', 'draft'), ('project_id', 'in', project_ids)], limit=5)
        overdue_installments = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date_due', '<', fields.Date.context_today(self)),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('installment_line_id.plan_id.unit_id.project_id', 'in', project_ids)
        ], limit=5)
        
        pending_list = []
        for insp in pending_inspections:
            pending_list.append({
                'id': insp.id,
                'name': insp.name,
                'project': insp.project_id.name,
                'milestone': insp.milestone_id.name
            })
            
        overdue_list = []
        for inv in overdue_installments:
            overdue_list.append({
                'id': inv.id,
                'name': inv.name,
                'client': inv.partner_id.name,
                'amount': f"{inv.amount_residual} {inv.currency_id.name}",
                'due': str(inv.invoice_date_due)
            })

        # 10. Progressive Site Intelligence (Project Albums)
        project_albums = []
        for proj in construction_projects:
            # Finding all images for this specific project
            proj_images = self.env['construction.project.image'].search([('project_id', '=', proj.id)], order='create_date desc')
            if proj_images:
                project_albums.append({
                    'id': proj.id,
                    'name': proj.name,
                    'cover_image_id': proj_images[0].id,
                    'count': len(proj_images),
                    'images': [{
                        'id': img.id,
                        'date': str(img.create_date.date())
                    } for img in proj_images]
                })

        return {
            'project_count': project_count,
            'task_count': task_count,
            'contractor_count': contractor_count,
            'job_order_count': job_order_count,
            'material_request_count': material_request_count,
            'inspection_count': inspection_count,
            'recent_visuals': project_albums,
            'charts': {
                'phase_labels': phase_labels,
                'phase_data': phase_data,
                'commercial_labels': commercial_labels,
                'commercial_data': commercial_data,
                'revenue': total_revenue,
                'expense': total_costs,
                'pending_inspections': pending_list,
                'contractor_pulse': contractor_pulse,
                'procurement_risks': risks,
                'procurement_analysis': procurement_analysis,
                'burn_data': burn_data,
                'overdue_installments': overdue_list,
                'sales_analysis': {
                    'labels': sales_labels,
                    'datasets': project_datasets
                },
                'realized_asset_value': realized_asset_value,
                'potential_asset_value': potential_asset_value,
                'sold_units': sold_units,
                'available_units': available_units
            }
        }
    @api.model
    def get_profitability_metrics(self, project_id=None):
        """ Specialized financial analysis looping through live procurement and certification data organic logically mathematical. """
        domain = [('project_type', '=', 'construction')]
        if project_id:
            domain.append(('id', '=', project_id))
        
        projects = self.env['project.project'].search(domain)
        
        results = []
        for proj in projects:
            # 1. Budgeted Cost from Cost Sheets
            cost_sheets = self.env['construction.cost.sheet'].search([('project_id', '=', proj.id)])
            total_budget = sum(cost_sheets.mapped('total_cost'))
            
            # Category Breakdown
            material_budget = sum(cost_sheets.mapped('material_budget_total'))
            labor_budget = sum(cost_sheets.mapped('labor_budget_total'))
            overhead_budget = sum(cost_sheets.mapped('overhead_budget_total'))
            fleet_budget = sum(cost_sheets.mapped('vehicle_budget_total'))
            equip_budget = sum(cost_sheets.mapped('equipment_budget_total'))
            
            # 2. Actual Spend from Analytic Distribution
            # We search for account.move.line where analytic account matches project's analytic account
            actual_costs = 0.0
            if proj.analytic_account_id:
                # Optimized search for analytic distribution hits
                # Odoo 16 stores analytic distribution as JSONB/Dict
                # We'll use a standard ORM approach to find lines linked to this analytic account
                lines = self.env['account.move.line'].search([
                    ('parent_state', '=', 'posted'),
                    ('move_id.move_type', 'in', ['in_invoice', 'in_refund']),
                ])
                # Filter lines where the project's analytic account ID is in the distribution keys
                analytic_id_str = str(proj.analytic_account_id.id)
                project_lines = lines.filtered(lambda l: l.analytic_distribution and analytic_id_str in l.analytic_distribution)
                actual_costs = sum(project_lines.mapped('balance')) # Balance for vendor bills is usually negative/debit
                # Ensure we handle sign convention (Expenses should be positive for dashboard metrics)
                actual_costs = abs(actual_costs)

            # 3. Certified & Retention (CPR)
            cprs = self.env['construction.cpr'].search([('project_id', '=', proj.id), ('state', 'not in', ['draft', 'cancel'])])
            total_certified = sum(cprs.mapped('gross_certified_amount'))
            total_retention = sum(cprs.mapped('retention_amount'))
            total_paid = sum(cprs.mapped('net_payable_amount')) # Net payable in invoiced/paid CPRs

            # 4. Profitability
            revenue = proj.total_collected # Existing compute field
            gross_margin = revenue - actual_costs
            margin_percent = (gross_margin / revenue * 100.0) if revenue > 0 else 0.0

            results.append({
                'project_id': proj.id,
                'project_name': proj.name,
                'budget': total_budget,
                'actual': actual_costs,
                'certified': total_certified,
                'retention': total_retention,
                'paid': total_paid,
                'revenue': revenue,
                'margin': gross_margin,
                'margin_percent': margin_percent,
                'variance': total_budget - actual_costs,
                'categories': {
                    'material': material_budget,
                    'labor': labor_budget,
                    'overhead': overhead_budget,
                    'fleet': fleet_budget,
                    'equipment': equip_budget,
                }
            })

        return results
