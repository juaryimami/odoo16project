from odoo import models, fields, api, _
import uuid
import werkzeug.urls
import json

class JobOrder(models.Model):
    _name = 'construction.job.order'
    _description = 'Contractor Job Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']

    name = fields.Char(string='Job Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='project_id.partner_id', store=True)
    inspector_id = fields.Many2one('res.partner', string='Project Inspector', related='project_id.inspector_id', store=True)
    
    lifecycle_id = fields.Many2one('construction.lifecycle', related='project_id.lifecycle_id', store=True)
    phase_id = fields.Many2one('construction.phase', string='Construction Phase', domain="[('lifecycle_id', '=', lifecycle_id)]")
    task_id = fields.Many2one('project.task', string='Task / Activity')
    
    # Assignees & Time
    user_ids = fields.Many2many('res.users', string='Assignees')
    date_deadline = fields.Date(string='Deadline')
    date_start_actual = fields.Datetime(string='Actual Start')
    date_finish_actual = fields.Datetime(string='Actual Finish')
    date_end = fields.Datetime(string='Ending Date')
    
    # Categorization
    tag_ids = fields.Many2many('project.tags', string='Tags')
    milestone_id = fields.Many2one('construction.job.milestone', string='Milestone', domain="[('job_order_id', '=', id)]") # For single select in UI
    cost_sheet_id = fields.Many2one('construction.cost.sheet', string='Job Cost Center', domain="[('project_id', '=', project_id)]")
    
    contractor_id = fields.Many2one('res.partner', string='Contractor', domain="[('is_contractor', '=', True)]", required=True, tracking=True)
    description = fields.Html(string='Work Description')
    agreed_rate = fields.Monetary(string='Agreed Rate', compute='_compute_agreed_rate', store=True, tracking=True)
    total_cost = fields.Monetary(string='Total Cost', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    contract_type = fields.Selection([
        ('full', 'Full Contract Agreement (All items Contractor covered)'),
        ('execution', 'Execution Contract (Material & Overhead Owner provided)')
    ], string='Agreement Type', default='execution', tracking=True)
    
    advance_payment_pct = fields.Float(string='Advance Payment %', default=30.0, help="Planned percentage of the total cost for mobilization.")
    portal_password = fields.Char(string='Portal Access Password', copy=False, help="Generated upon acceptance for secure execution dashboard access.")
    
    # Hierarchy
    parent_id = fields.Many2one('construction.job.order', string='Parent Job')
    child_ids = fields.One2many('construction.job.order', 'parent_id', string='Subtasks')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('offered', 'Offered'),
        ('accepted', 'Accepted'),
        ('active', 'In Progress'),
        ('ready_for_inspection', 'Ready for Inspection'),
        ('approved', 'Quality Approved'),
        ('rework', 'Rework Required'),
        ('completed', 'Done'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)
    
    access_token = fields.Char(string='Access Token', copy=False, default=lambda self: str(uuid.uuid4()))
    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)
    portal_url = fields.Char(string='Portal link', compute='_compute_portal_url')
    is_budget_synced = fields.Boolean(string='Budget Synced', default=False, copy=False)
    pm_name = fields.Char(string='Authorized By (PM)')
    pm_signature = fields.Binary(string='PM Digital Signature')

    def _compute_portal_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for order in self:
            order.portal_url = "%s/job_offer/%s" % (base_url, order.access_token)

    # Resource Tabs
    material_plan_ids = fields.One2many('construction.job.material.line', 'job_order_id', string='Material Planning')
    material_consumed_ids = fields.One2many('construction.job.consumption.line', 'job_order_id', string='Consumed Materials')
    vehicle_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Vehicles', domain=[('resource_type', '=', 'vehicle')])
    equipment_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Equipment', domain=[('resource_type', '=', 'equipment')])
    expense_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Expenses', domain=[('resource_type', '=', 'expense')])
    labor_budget_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Labor Budget', domain=[('resource_type', '=', 'labor')])
    overhead_budget_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Overhead Budget', domain=[('resource_type', '=', 'overhead')])
    
    checklist_template_id = fields.Many2one('construction.checklist.template', string='Checklist Template')
    checklist_ids = fields.One2many('construction.job.checklist.line', 'job_order_id', string='Checklist Items')
    daily_log_ids = fields.One2many('construction.daily.log', 'job_order_id', string='Daily Logs')
    site_expense_ids = fields.One2many('construction.site.expense', 'job_order_id', string='Site Expenses')
    extra_info = fields.Text(string='Extra Info')

    # Labor / Timesheet Integration
    timesheet_ids = fields.One2many('account.analytic.line', 'job_order_id', string='Timesheets')

    # Financial Aggregation
    total_material_cost = fields.Monetary(string='Material Cost', compute='_compute_total_costs', store=True)
    total_resource_cost = fields.Monetary(string='Resource Cost', compute='_compute_total_costs', store=True)
    total_labor_cost = fields.Monetary(string='Labor Cost', compute='_compute_total_costs', store=True)
    actual_total_cost = fields.Monetary(string='Actual Total Cost', compute='_compute_total_costs', store=True)

    # Budget Review Analysis (Planned Costs)
    planned_material_cost = fields.Monetary(string='Planned Material', compute='_compute_budget_analysis')
    planned_fleet_cost = fields.Monetary(string='Planned Fleet', compute='_compute_budget_analysis')
    planned_equipment_cost = fields.Monetary(string='Planned Equipment', compute='_compute_budget_analysis')
    planned_labor_cost = fields.Monetary(string='Planned Labor', compute='_compute_budget_analysis')
    planned_overhead_cost = fields.Monetary(string='Planned Overhead', compute='_compute_budget_analysis')
    planned_resource_total = fields.Monetary(string='Total Resource Planned Value', compute='_compute_budget_analysis')
    total_planned_budget = fields.Monetary(string='Total Planned Budget', compute='_compute_budget_analysis')
    budget_profit_margin = fields.Monetary(string='Profit Margin', compute='_compute_budget_analysis')
    budget_utilization_ratio = fields.Float(string='Budget Utilization %', compute='_compute_budget_analysis')

    # New Actual Spend Category Totals (Computed from PAID Vendor Bills)
    actual_material_spend = fields.Monetary(string='Actual Material', compute='_compute_actual_spend_totals')
    actual_fleet_spend = fields.Monetary(string='Actual Fleet', compute='_compute_actual_spend_totals')
    actual_equipment_spend = fields.Monetary(string='Actual Equipment', compute='_compute_actual_spend_totals')
    actual_labor_spend = fields.Monetary(string='Actual Labor', compute='_compute_actual_spend_totals')
    actual_overhead_spend = fields.Monetary(string='Actual Overhead', compute='_compute_actual_spend_totals')
    total_actual_spend = fields.Monetary(string='Total Actual Spent', compute='_compute_actual_spend_totals')
    
    budget_utilization_pct = fields.Float(string='Actual Budget Utilization (%)', compute='_compute_actual_spend_totals')
    
    # Category utilization percentages for the "graph" view
    utilization_material = fields.Float(compute='_compute_category_utilization')
    utilization_fleet = fields.Float(compute='_compute_category_utilization')
    utilization_equipment = fields.Float(compute='_compute_category_utilization')
    utilization_labor = fields.Float(compute='_compute_category_utilization')
    utilization_overhead = fields.Float(compute='_compute_category_utilization')
    budget_analysis_chart_data = fields.Text(string='Budget Analysis Chart', compute='_compute_budget_chart_data')

    @api.depends('contract_type', 'material_plan_ids.cost', 'vehicle_line_ids.total_cost', 
                 'equipment_line_ids.total_cost', 'labor_budget_line_ids.total_cost', 
                 'overhead_budget_line_ids.total_cost')
    def _compute_agreed_rate(self):
        for record in self:
            mat = sum(record.material_plan_ids.mapped('cost'))
            flt = sum(record.vehicle_line_ids.mapped('total_cost'))
            eqp = sum(record.equipment_line_ids.mapped('total_cost'))
            lbr = sum(record.labor_budget_line_ids.mapped('total_cost'))
            ovh = sum(record.overhead_budget_line_ids.mapped('total_cost'))
            
            if record.contract_type == 'full':
                record.agreed_rate = mat + flt + eqp + lbr + ovh
            else:
                # Execution contract: only contractor-provided resources (Labor, Equipment, Fleet)
                record.agreed_rate = lbr + eqp + flt

    @api.depends('material_plan_ids.cost', 'vehicle_line_ids.total_cost', 'equipment_line_ids.total_cost', 
                 'labor_budget_line_ids.total_cost', 'overhead_budget_line_ids.total_cost', 'agreed_rate')
    def _compute_budget_analysis(self):
        for record in self:
            mat = sum(record.material_plan_ids.mapped('cost'))
            flt = sum(record.vehicle_line_ids.mapped('total_cost'))
            eqp = sum(record.equipment_line_ids.mapped('total_cost'))
            lbr = sum(record.labor_budget_line_ids.mapped('total_cost'))
            ovh = sum(record.overhead_budget_line_ids.mapped('total_cost'))
            
            record.planned_material_cost = mat
            record.planned_fleet_cost = flt
            record.planned_equipment_cost = eqp
            record.planned_labor_cost = lbr
            record.planned_overhead_cost = ovh
            record.planned_resource_total = flt + eqp + lbr
            
            total = mat + flt + eqp + lbr + ovh
            record.total_planned_budget = total
            record.budget_profit_margin = record.agreed_rate - total
            record.budget_utilization_ratio = (total / record.agreed_rate * 100) if record.agreed_rate else 0.0

    @api.depends('material_consumed_ids.cost', 'vehicle_line_ids.total_cost', 'equipment_line_ids.total_cost', 'expense_line_ids.total_cost', 'timesheet_ids.amount')
    def _compute_total_costs(self):
        for record in self:
            mat_cost = sum(record.material_consumed_ids.mapped('cost'))
            res_cost = sum(record.vehicle_line_ids.mapped('total_cost')) + \
                       sum(record.equipment_line_ids.mapped('total_cost')) + \
                       sum(record.expense_line_ids.mapped('actual_amount')) + \
                       sum(record.overhead_budget_line_ids.mapped('actual_amount'))
            labor_cost = abs(sum(record.timesheet_ids.mapped('amount')))
            
            record.total_material_cost = mat_cost
            record.total_resource_cost = res_cost
            record.total_labor_cost = labor_cost
            record.actual_total_cost = mat_cost + res_cost + labor_cost

    @api.depends('cost_sheet_id', 'total_planned_budget')
    def _compute_actual_spend_totals(self):
        for order in self:
            # Initialize totals
            totals = {
                'material': 0.0,
                'fleet': 0.0,
                'equipment': 0.0,
                'labor': 0.0,
                'overhead': 0.0
            }
            
            # 1. External Spend (Vendor Bills linked to this Job Order)
            # We search for ALL posted bill lines for this JO
            move_lines = self.env['account.move.line'].search([
                ('move_id.job_order_id', '=', order.id),
                ('parent_state', '=', 'posted'),
                ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])
            ])
            
            for line in move_lines:
                amount = line.price_subtotal if line.move_id.move_type == 'in_invoice' else -line.price_subtotal
                
                # Determine Category from Reference
                ref = line.cost_line_id_ref
                if ref:
                    model_name = ref._name
                    if model_name == 'construction.cost.material.line':
                        totals['material'] += amount
                    elif model_name == 'construction.cost.labor.line':
                        totals['labor'] += amount
                    elif model_name == 'construction.cost.equipment.line':
                        totals['equipment'] += amount
                    elif model_name == 'construction.cost.vehicle.line':
                        totals['fleet'] += amount
                    elif model_name == 'construction.cost.overhead.line':
                        totals['overhead'] += amount
                    elif model_name == 'construction.job.resource.line':
                        # Site Expenses are often linked to Job Resource Lines
                        if ref.resource_type == 'overhead':
                            totals['overhead'] += amount
                        elif ref.resource_type == 'labor':
                            totals['labor'] += amount
                        elif ref.resource_type == 'equipment':
                            totals['equipment'] += amount
                        elif ref.resource_type == 'fleet':
                            totals['fleet'] += amount
                else:
                    # Fallback: Check where this product belongs in the Project's Master Cost Sheet
                    product = line.product_id
                    project = order.project_id
                    if product:
                        # 1. Check Material Budget
                        if self.env['construction.cost.material.line'].search_count([
                            ('product_id', '=', product.id),
                            ('cost_sheet_id.project_id', '=', project.id)
                        ]):
                            totals['material'] += amount
                        # 2. Check Labor Budget
                        elif self.env['construction.cost.labor.line'].search_count([
                            ('product_id', '=', product.id),
                            ('cost_sheet_id.project_id', '=', project.id)
                        ]):
                            totals['labor'] += amount
                        # 3. Check Equipment Budget
                        elif self.env['construction.cost.equipment.line'].search_count([
                            ('product_id', '=', product.id),
                            ('cost_sheet_id.project_id', '=', project.id)
                        ]):
                            totals['equipment'] += amount
                        # 4. Check Vehicle/Fleet Budget
                        elif self.env['construction.cost.vehicle.line'].search_count([
                            ('vehicle_id', '=', product.id),
                            ('cost_sheet_id.project_id', '=', project.id)
                        ]):
                            totals['fleet'] += amount
                        else:
                            # 5. Last resort: Try category name
                            cat_name = product.categ_id.name.lower() if product.categ_id else ''
                            if 'material' in cat_name: totals['material'] += amount
                            elif 'labor' in cat_name: totals['labor'] += amount
                            elif 'equipment' in cat_name: totals['equipment'] += amount
                            elif 'fleet' in cat_name or 'vehicle' in cat_name: totals['fleet'] += amount
                            else: totals['overhead'] += amount
                    else:
                        totals['overhead'] += amount

            # 2. Internal Spend (Material Consumptions)
            # These are internal stock moves, not bills
            consumed = self.env['construction.job.material.line'].search([
                ('job_order_id', '=', order.id),
                ('is_consumed', '=', True)
            ])
            totals['material'] += sum(consumed.mapped('cost'))

            # Apply totals
            order.actual_material_spend = totals['material']
            order.actual_fleet_spend = totals['fleet']
            order.actual_equipment_spend = totals['equipment']
            order.actual_labor_spend = totals['labor']
            order.actual_overhead_spend = totals['overhead']
            
            total = sum(totals.values())
            order.total_actual_spend = total
            order.budget_utilization_pct = (total / order.total_planned_budget * 100) if order.total_planned_budget else 0.0

    @api.depends('actual_material_spend', 'actual_fleet_spend', 'actual_equipment_spend', 'actual_labor_spend', 'actual_overhead_spend',
                 'planned_material_cost', 'planned_fleet_cost', 'planned_equipment_cost', 'planned_labor_cost', 'planned_overhead_cost')
    def _compute_budget_chart_data(self):
        for order in self:
            data = {
                'labels': ['Material', 'Fleet', 'Equipment', 'Labor', 'Overhead'],
                'datasets': [
                    {
                        'label': 'Planned',
                        'data': [
                            order.planned_material_cost,
                            order.planned_fleet_cost,
                            order.planned_equipment_cost,
                            order.planned_labor_cost,
                            order.planned_overhead_cost
                        ],
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                        'borderColor': 'rgba(54, 162, 235, 1)',
                        'borderWidth': 1
                    },
                    {
                        'label': 'Actual',
                        'data': [
                            order.actual_material_spend,
                            order.actual_fleet_spend,
                            order.actual_equipment_spend,
                            order.actual_labor_spend,
                            order.actual_overhead_spend
                        ],
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'borderWidth': 1
                    }
                ]
            }
            order.budget_analysis_chart_data = json.dumps(data)

    @api.depends('actual_material_spend', 'actual_fleet_spend', 'actual_equipment_spend', 'actual_labor_spend', 'actual_overhead_spend',
                 'planned_material_cost', 'planned_fleet_cost', 'planned_equipment_cost', 'planned_labor_cost', 'planned_overhead_cost')
    def _compute_category_utilization(self):
        for order in self:
            def get_pct(actual, planned):
                return (actual / planned * 100) if planned > 0 else (100.0 if actual > 0 else 0.0)
            
            order.utilization_material = get_pct(order.actual_material_spend, order.planned_material_cost)
            order.utilization_fleet = get_pct(order.actual_fleet_spend, order.planned_fleet_cost)
            order.utilization_equipment = get_pct(order.actual_equipment_spend, order.planned_equipment_cost)
            order.utilization_labor = get_pct(order.actual_labor_spend, order.planned_labor_cost)
            order.utilization_overhead = get_pct(order.actual_overhead_spend, order.planned_overhead_cost)

    # Counters
    invoice_count = fields.Integer(compute='_compute_counts')
    inspection_count = fields.Integer(compute='_compute_counts')
    estimate_count = fields.Integer(compute='_compute_counts')
    requisition_count = fields.Integer(compute='_compute_counts')
    cpr_count = fields.Integer(compute='_compute_counts')
    picking_count = fields.Integer(compute='_compute_counts')
    issue_request_count = fields.Integer(compute='_compute_counts')
    on_hand_count = fields.Integer(compute='_compute_counts', string='On Hand Qty')
    checklist_count = fields.Integer(compute='_compute_counts')
    timesheet_count = fields.Integer(compute='_compute_counts')
    expense_count = fields.Integer(compute='_compute_counts')
    daily_log_count = fields.Integer(compute='_compute_counts', string='Daily Logs Count')

    is_inspected_passed = fields.Boolean(compute='_compute_is_passed', string='Passed Inspection')
    progress_ratio = fields.Float(compute='_compute_is_passed', string='Job Completion (%)')

    milestone_ids = fields.One2many('construction.job.milestone', 'job_order_id', string='Execution Milestones')
    payment_ids = fields.One2many('construction.job.payment', 'job_order_id', string='Financial Payments')
    current_milestone_id = fields.Many2one('construction.job.milestone', string='Active Phase', compute='_compute_current_milestone', store=True)

    @api.depends('milestone_ids.state')
    def _compute_current_milestone(self):
        for order in self:
            # Active phase is the first one in_progress or the first pending
            order.current_milestone_id = order.milestone_ids.filtered(lambda m: m.state == 'in_progress')[:1] or \
                                       order.milestone_ids.filtered(lambda m: m.state == 'pending')[:1]
    
    milestone_progress_data = fields.Text(compute='_compute_milestone_progress_data')
    payment_request_ids = fields.One2many('construction.cpr', 'job_order_id', string='Payment Requests')
    payment_request_count = fields.Integer(compute='_compute_payment_request_count')

    @api.depends('payment_request_ids')
    def _compute_payment_request_count(self):
        for record in self:
            record.payment_request_count = len(record.payment_request_ids)

    total_certified_progress = fields.Float(string='Total Certified Progress (%)', compute='_compute_total_certified_progress')

    @api.depends('payment_request_ids.state', 'payment_request_ids.certified_progress', 'payment_request_ids.previous_certified_progress')
    def _compute_total_certified_progress(self):
        for order in self:
            approved_cprs = order.payment_request_ids.filtered(lambda p: p.state in ['approved', 'invoiced', 'paid'])
            total = sum(p.certified_progress - p.previous_certified_progress for p in approved_cprs)
            order.total_certified_progress = total

    total_paid_amount = fields.Monetary(string='Total Paid to Date', compute='_compute_financial_summary', currency_field='currency_id')
    total_retention_amount = fields.Monetary(string='Total Retention Fund', compute='_compute_financial_summary', currency_field='currency_id')

    @api.depends('payment_request_ids.state', 'payment_request_ids.invoice_id.payment_state', 'payment_request_ids.net_payable_amount', 'payment_request_ids.retention_amount')
    def _compute_financial_summary(self):
        for order in self:
            # 1. Net Paid: Only sum CPRs that are either marked as paid OR have a paid invoice
            paid_cprs = order.payment_request_ids.filtered(lambda p: p.state == 'paid' or (p.invoice_id and p.invoice_id.payment_state in ['paid', 'in_payment']))
            order.total_paid_amount = sum(paid_cprs.mapped('net_payable_amount'))
            
            # 2. Retention: Sum all approved work that hasn't been cancelled
            valid_cprs = order.payment_request_ids.filtered(lambda p: p.state in ['approved', 'invoiced', 'paid'])
            order.total_retention_amount = sum(valid_cprs.mapped('retention_amount'))

    def action_view_payment_requests(self):
        self.ensure_one()
        return {
            'name': _('Contractor Payment Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.cpr',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id, 'default_project_id': self.project_id.id},
        }

    def action_view_inspections(self):
        self.ensure_one()
        return {
            'name': _('Quality Inspections'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.inspection',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id, 'default_project_id': self.project_id.id},
        }

    def action_view_estimates(self):
        self.ensure_one()
        return {
            'name': _('Cost Estimations / BOQ'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.estimate',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id, 'default_project_id': self.project_id.id},
        }

    @api.depends('milestone_ids.state', 'milestone_ids.percentage', 'milestone_ids.sequence', 'milestone_ids.description', 'milestone_ids.checklist_ids', 'milestone_ids.checklist_ids.is_done', 'milestone_ids.milestone_type')
    def _compute_milestone_progress_data(self):
        for order in self:
            milestones = []
            # Only show WORK milestones in the execution roadmap
            work_milestones = order.milestone_ids.filtered(lambda m: m.milestone_type == 'work').sorted('sequence')
            for m in work_milestones:
                total_checks = len(m.checklist_ids)
                passed_checks = len(m.checklist_ids.filtered(lambda c: c.is_done))
                milestones.append({
                    'id': m.id,
                    'name': m.name,
                    'state': m.state,
                    'percentage': m.percentage,
                    'description': m.description or '',
                    'has_checklist': total_checks > 0,
                    'checklist_summary': f"{passed_checks}/{total_checks}" if total_checks > 0 else "",
                    'is_current': m.id == order.current_milestone_id.id,
                    'sequence': m.sequence
                })
            order.milestone_progress_data = json.dumps(milestones)
    
    def _resequence_milestones(self):
        self.ensure_one()
        work_milestones = self.milestone_ids.filtered(lambda m: m.milestone_type == 'work').sorted('sequence')
        for i, m in enumerate(work_milestones):
            m.sequence = (i + 1) * 10
    
    picking_ids = fields.One2many('stock.picking', 'job_order_id', string='Stock Pickings')

    @api.onchange('checklist_template_id')
    def _onchange_checklist_template_id(self):
        if self.checklist_template_id:
            lines = []
            for line in self.checklist_template_id.line_ids:
                lines.append((0, 0, {
                    'name': line.name,
                    'mandatory': line.mandatory,
                    'sequence': line.sequence
                }))
            self.checklist_ids = [(5, 0, 0)] + lines

    @api.depends('checklist_ids', 'checklist_ids.is_done')
    @api.depends('state', 'checklist_ids.is_done', 'milestone_ids.state', 'milestone_ids.percentage')
    def _compute_is_passed(self):
        for order in self:
            if order.state in ['completed', 'closed']:
                order.is_inspected_passed = True
                order.progress_ratio = 100.0
                continue
            
            # Scenario A: Milestone-driven Progress (Priority)
            if order.milestone_ids:
                total_weight = sum(order.milestone_ids.mapped('percentage')) or 100.0
                approved_weight = sum(order.milestone_ids.filtered(lambda m: m.state in ['approved', 'billed']).mapped('percentage'))
                order.progress_ratio = (approved_weight / total_weight) * 100.0
                order.is_inspected_passed = order.progress_ratio >= 100.0
            
            # Scenario B: Checklist-driven Progress (Fallback)
            elif order.checklist_ids:
                total = len(order.checklist_ids)
                passed = len(order.checklist_ids.filtered(lambda c: c.is_done))
                order.progress_ratio = (passed / total) * 100.0 if total > 0 else 0.0
                order.is_inspected_passed = passed == total if total > 0 else False
            else:
                order.progress_ratio = 0.0
                order.is_inspected_passed = False

    def _compute_counts(self):
        for order in self:
            order.requisition_count = self.env['construction.material.requisition'].search_count([('job_order_id', '=', order.id)])
            order.cpr_count = self.env['construction.cpr'].search_count([('job_order_id', '=', order.id)])
            order.inspection_count = self.env['construction.inspection'].search_count([('job_order_id', '=', order.id)])
            order.estimate_count = self.env['construction.estimate'].search_count([('job_order_id', '=', order.id)])
            order.invoice_count = len(self.env['account.move'].search([('job_order_id', '=', order.id)]))
            order.picking_count = self.env['stock.picking'].search_count([('job_order_id', '=', order.id)])
            order.issue_request_count = self.env['construction.material.issue.request'].search_count([('job_order_id', '=', order.id)])
            order.checklist_count = len(order.checklist_ids)
            order.timesheet_count = len(order.timesheet_ids)
            order.expense_count = self.env['construction.site.expense'].search_count([('job_order_id', '=', order.id)])
            order.daily_log_count = len(order.daily_log_ids)
            # Calculate count of distinct PLANNED materials on hand in warehouse
            products = order.material_plan_ids.mapped('product_id')
            location = order.project_id.warehouse_id.lot_stock_id
            if products and location:
                quants = self.env['stock.quant'].sudo().search([
                    ('product_id', 'in', products.ids),
                    ('location_id', 'child_of', location.id)
                ])
                # Count distinct products with positive quantity
                products_with_stock = quants.filtered(lambda q: q.quantity > 0.0).mapped('product_id')
                order.on_hand_count = len(products_with_stock)
            else:
                order.on_hand_count = 0

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['domain'] = [('job_order_id', '=', self.id)]
        action['context'] = {'default_job_order_id': self.id}
        return action

    def action_open_checklist(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quality Checklist'),
            'res_model': 'construction.job.checklist.line',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id},
        }

    def action_open_site_expenses(self):
        self.ensure_one()
        return {
            'name': _('Site Expenses'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.site.expense',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id, 'default_project_id': self.project_id.id},
        }

    def action_open_timesheets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Labor Timesheets'),
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id},
        }

    def action_view_on_hand(self):
        self.ensure_one()
        products = self.material_plan_ids.mapped('product_id')
        location = self.project_id.warehouse_id.lot_stock_id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('On Hand Quantity (Site-Specific)'),
            'res_model': 'stock.quant',
            'view_mode': 'tree,pivot,form',
            'domain': [
                ('product_id', 'in', products.ids),
                ('location_id', 'child_of', location.id)
            ],
            'context': {
                'search_default_internal_loc': 1,
                'search_default_productgroup': 1,
                'default_location_id': location.id,
            },
        }

    def action_open_material_requisitions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Material Requisitions'),
            'res_model': 'construction.material.requisition',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id, 'default_project_id': self.project_id.id},
        }

    def action_open_site_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Site Expenses'),
            'res_model': 'construction.site.expense',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id},
        }

    def action_add_daily_log(self):
        self.ensure_one()
        return {
            'name': _('Add Daily Log'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.daily.log',
            'view_mode': 'form',
            'context': {
                'default_job_order_id': self.id,
                'default_project_id': self.project_id.id,
                'default_phase_id': self.phase_id.id,
            },
            'target': 'current',
        }

    def action_add_material_requisition(self):
        self.ensure_one()
        return {
            'name': _('Material Requisition'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.material.requisition',
            'view_mode': 'form',
            'context': {
                'default_job_order_id': self.id,
                'default_project_id': self.project_id.id,
            },
            'target': 'current',
        }

    def action_add_site_expense(self):
        self.ensure_one()
        return {
            'name': _('Add Site Expense'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.site.expense',
            'view_mode': 'form',
            'context': {
                'default_job_order_id': self.id,
                'default_project_id': self.project_id.id,
            },
            'target': 'current',
        }

    def action_view_daily_logs(self):
        self.ensure_one()
        return {
            'name': _('Daily Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.daily.log',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id},
        }
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Site Expenses'),
            'res_model': 'construction.job.resource.line',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id), ('resource_type', '=', 'expense')],
            'context': {'default_job_order_id': self.id, 'default_resource_type': 'expense'},
        }

    def action_load_from_cost_sheet(self):
        self.ensure_one()
        if not self.cost_sheet_id:
            from odoo.exceptions import UserError
            raise UserError(_("Please select a Job Cost Center (Master Budget) before loading."))
        
        # 1. Load Planned Materials
        mat_domain = [('cost_sheet_id', '=', self.cost_sheet_id.id)]
        if self.phase_id:
            mat_domain.append(('phase_id', '=', self.phase_id.id))
        
        mat_lines = self.env['construction.cost.material.line'].search(mat_domain)
        mat_vals = []
        for line in mat_lines:
            mat_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'unit_price': line.cost_unit,
                'cost_line_id': line.id,
                'is_consumed': False,
                'provided_by': 'owner' if self.contract_type == 'execution' else 'contractor',
            }))
        
        # 2. Load Planned Equipment & Vehicles
        res_vals = []
        
        # Equipment
        eq_lines = self.env['construction.cost.equipment.line'].search(mat_domain)
        for line in eq_lines:
            res_vals.append((0, 0, {
                'resource_type': 'equipment',
                'name': line.equipment_id.name if line.equipment_id else line.description,
                'quantity': line.quantity,
                'unit_cost': line.cost_unit,
                'cost_line_type': 'construction.cost.equipment.line',
                'cost_line_id': line.id,
                'unit': 'hour' if line.rate_type == 'hourly' else 'day',
            }))
            
        # Vehicles
        vh_lines = self.env['construction.cost.vehicle.line'].search(mat_domain)
        for line in vh_lines:
            res_vals.append((0, 0, {
                'resource_type': 'vehicle',
                'name': line.vehicle_id.name if line.vehicle_id else line.description,
                'quantity': line.quantity,
                'unit_cost': line.cost_unit,
                'cost_line_type': 'construction.cost.vehicle.line',
                'cost_line_id': line.id,
                'unit': 'unit',
            }))

        # 3. Load Labor Plans
        labor_lines = self.env['construction.cost.labor.line'].search(mat_domain)
        for line in labor_lines:
            res_vals.append((0, 0, {
                'resource_type': 'labor',
                'name': f"{line.role_id.name or 'Labor'} - {line.employee_count} Persons",
                'quantity': line.employee_count * line.hours_per_person,
                'unit_cost': line.cost_unit,
                'unit': 'hour',
                'cost_line_type': 'construction.cost.labor.line',
                'cost_line_id': line.id,
            }))

        # 4. Load Overhead Plans
        ovh_lines = self.env['construction.cost.overhead.line'].search(mat_domain)
        for line in ovh_lines:
            res_vals.append((0, 0, {
                'resource_type': 'overhead',
                'name': line.description or 'Overhead Item',
                'quantity': line.quantity,
                'unit_cost': line.cost_unit,
                'unit': 'unit',
                'cost_line_type': 'construction.cost.overhead.line',
                'cost_line_id': line.id,
                'provided_by': 'owner' if self.contract_type == 'execution' else 'contractor',
            }))

        # Update Job Order Collections
        self.write({
            'material_plan_ids': [(5, 0, 0)] + mat_vals,
            'equipment_line_ids': [(5, 0, 0)] + [v for v in res_vals if v[2]['resource_type'] == 'equipment'],
            'vehicle_line_ids': [(5, 0, 0)] + [v for v in res_vals if v[2]['resource_type'] == 'vehicle'],
            'labor_budget_line_ids': [(5, 0, 0)] + [v for v in res_vals if v[2]['resource_type'] == 'labor'],
            'overhead_budget_line_ids': [(5, 0, 0)] + [v for v in res_vals if v[2]['resource_type'] == 'overhead'],
            'is_budget_synced': True,
        })
        
        return True

    def action_create_subtask(self):
        self.ensure_one()
        return {
            'name': _('Create Subtask'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.job.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_id': self.id,
                'default_project_id': self.project_id.id,
                'default_phase_id': self.phase_id.id,
            }
        }

    def action_create_picking(self):
        self.ensure_one()
        if not self.material_plan_ids:
            from odoo.exceptions import UserError
            raise UserError(_("There are no planned materials on this Job Order to request."))
        
        # Create a Draft Material Issue Request pre-filled with the planning lines
        vals = {
            'job_order_id': self.id,
            'request_type': 'delivery', # default
            'description': _('Auto-generated Material Request for Job Order %s') % self.name,
            'time_needed': fields.Datetime.now(),
            'state': 'draft',
            'line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'product_uom_id': line.product_uom_id.id,
            }) for line in self.material_plan_ids]
        }
        request = self.env['construction.material.issue.request'].create(vals)
        
        return {
            'name': _('Material Stock Issue Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.material.issue.request',
            'res_id': request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_material_issue_requests(self):
        self.ensure_one()
        return {
            'name': _('Material Issue Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.material.issue.request',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id},
        }

    def action_return_to_warehouse(self):
        self.ensure_one()
        if not self.project_id.warehouse_id:
            from odoo.exceptions import UserError
            raise UserError(_("Logistics Error: No 'Dedicated Site Warehouse' found for project '%s'. Please assign a warehouse in the Project form before generating pickings.") % self.project_id.name)

        # Try to find the internal picking type for the specific project warehouse
        project_wh = self.project_id.warehouse_id
        picking_type = project_wh.int_type_id
        
        if not picking_type:
            # Fallback search by code
            picking_type = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', project_wh.id),
                ('code', '=', 'internal')
            ], limit=1)
        
        if not picking_type:
            # Fallback to general internal picking type
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

        source_location = self.project_id.warehouse_id.lot_stock_id
        dest_location = picking_type.default_location_src_id if picking_type else False
        
        if not source_location or not dest_location:
             from odoo.exceptions import UserError
             raise UserError(_("Logistics Error: A valid Return Destination (Source Location of Internal Picking Type) must be set. Please check warehouse configurations."))

        # Create a Return picking (Internal Site -> Main Warehouse)
        picking = self.env['stock.picking'].create({
            'job_order_id': self.id,
            'project_id': self.project_id.id,
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'move_ids_without_package': [(0, 0, {
                'name': line.product_id.name + " (Return)",
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
            }) for line in self.material_consumed_ids]
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
        }

    def action_open_notes(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    def action_open_material_requisitions(self):
        self.ensure_one()
        return {
            'name': _('Material Requisitions'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.material.requisition',
            'view_mode': 'tree,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {
                'default_job_order_id': self.id,
                'default_project_id': self.project_id.id,
                'default_phase_id': self.phase_id.id,
            },
        }

    def action_offer(self):
        self.ensure_one()
        from odoo.exceptions import UserError
        
        if not self.contractor_id:
            raise UserError(_("Please select a contractor before making an offer."))
        
        if not self.date_deadline:
            raise UserError(_("Please set a Job Deadline before making an offer to ensure formal project timelines."))
        
        if not self.cost_sheet_id:
            raise UserError(_("Please assign a Budget Center before making an offer."))
            
        if self.cost_sheet_id.state != 'approved':
            raise UserError(_("The assigned Budget Center (%s) must be in 'Approved' state before offering the job.") % self.cost_sheet_id.name)
        
        # Ensure token exists
        if not self.access_token:
            self.access_token = str(uuid.uuid4())
            
        template = self.env.ref('construction_erp.email_template_job_order_offer_v3', raise_if_not_found=False)
        return {
            'name': _('Offer Job to Contractor'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.job.offer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_job_order_id': self.id,
                'default_email_template_id': template.id if template else False,
                'default_subject': _("Contract Offer: %s - %s") % (self.name, self.project_id.name or '') if template else '',
                'default_body': template._render_field('body_html', self.ids)[self.id] if template else '',
                'default_advance_payment_pct': self.advance_payment_pct,
            }
        }

    def action_accept(self):
        import secrets
        import string
        for record in self:
            # 1. Generate Secure Password for Execution Portal
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(8))
            
            record.write({
                'state': 'accepted',
                'portal_password': password
            })
            
            # Refined Payment Engine: Automated Advance CPR creation
            if record.advance_payment_pct > 0:
                advance_cpr = self.env['construction.cpr'].create({
                    'job_order_id': record.id,
                    'project_id': record.project_id.id,
                    'cpr_type': 'advance',
                    'current_progress_claim': record.advance_payment_pct,
                    'certified_progress': record.advance_payment_pct,
                    'state': 'draft'
                })
                # Populate Lines before verification
                advance_cpr.action_populate_lines()
                
                # Move to verify (which for advance auto-approves)
                advance_cpr.action_verify()
                # Create Vendor Bill immediately
                advance_cpr.action_create_bill()
                record.message_post(body=_("Mobilization Payment Certification (%s%%) generated automatically.") % record.advance_payment_pct)
            
            # 2. Trigger Congratulations & Access Email + Chatter Post
            template = self.env.ref('construction_erp.email_template_job_order_accepted', raise_if_not_found=False)
            if template:
                # Render the high-fidelity template body for the chatter
                body_html = template._render_field('body_html', record.ids)[record.id]
                
                # Send the Actual Email
                template.send_mail(record.id, force_send=True)
                
                # Post the same premium design to Chatter
                record.message_post(
                    body=body_html,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
            else:
                # Fallback to simple message if template is missing
                record.message_post(body=_("<b>Congratulations! Job Accepted by %s.</b><br/>"
                                           "<b>Execution Portal Access:</b><br/>"
                                           "Link: <a href='%s'>%s</a><br/>"
                                           "Password: <code>%s</code>") % 
                                           (record.contractor_id.name, record.portal_url, record.portal_url, password))


    def action_start(self):
        for record in self:
            record.state = 'active'
            record.date_start_actual = fields.Datetime.now()
            # Activate first milestone
            if record.milestone_ids:
                first_ms = record.milestone_ids.sorted('sequence')[:1]
                if first_ms.state == 'pending':
                    first_ms.state = 'in_progress'
            record.message_post(body=_("Mobilization started - Execution tracking system activated."))

    def action_complete(self):
        from odoo.exceptions import UserError
        for record in self:
            if not record.inspector_id:
                raise UserError(_("Please assign a Project Inspector in the project settings before reporting finish."))
            if not record.checklist_ids:
                raise UserError(_("No checklist items found. Please add quality checks or load a template."))

            # Create Inspection with Token (DRAFT state until email sent)
            inspection_vals = {
                'job_order_id': record.id,
                'project_id': record.project_id.id,
                'phase_id': record.phase_id.id,
                'task_id': record.task_id.id,
                'inspector_id': record.inspector_id.id,
                'milestone_id': record.milestone_id.id if record.milestone_id else False,
                'access_token': str(uuid.uuid4()),
                'line_ids': []
            }
            
            # Copy only items that are NOT DONE (Handles rework history)
            for item in record.checklist_ids.filtered(lambda c: not c.is_done):
                inspection_vals['line_ids'].append((0, 0, {
                    'checklist_line_id': item.id,
                }))
            
            inspection = self.env['construction.inspection'].create(inspection_vals)
            
            # 3. Open the Inspection Gate Wizard
            template = self.env.ref('construction_erp.email_template_quality_inspection_request', raise_if_not_found=False)
            
            return {
                'name': _("Inspection Gate: Formal Request Review"),
                'type': 'ir.actions.act_window',
                'res_model': 'construction.inspection.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_job_order_id': record.id,
                    'default_inspection_id': inspection.id,
                    'default_phase_id': record.phase_id.id,
                    'default_subject': template._render_field('subject', [inspection.id])[inspection.id] if template else _("Quality Inspection Request"),
                    'default_body': template._render_field('body_html', [inspection.id])[inspection.id] if template else "",
                }
            }

    def action_mark_done(self):
        for record in self:
            if record.progress_ratio < 100.0:
                 raise ValidationError(_("Cannot close Job Order: Work progress is at %.2f%%. 100%% completion required.") % record.progress_ratio)
            record.state = 'completed'
            # Expire Portal Access Token on 100% completion
            record.access_token = False
            record.message_post(body=_("Job Order 100% Completed. Contractor Portal Access Invalidated for security."))

    def action_rework(self):
        for record in self:
            record.state = 'active'
            record.message_post(body=_("Inspector requested rework. Job returned to In Progress state."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.job.order') or _('New')
        records = super(JobOrder, self).create(vals_list)
        for record in records:
            # NOTIFICATION: Job Order Created
            if record.project_id.user_id:
                record.send_in_app_notification(
                    record.project_id.user_id,
                    _("New Job Order '%s' has been created for project '%s'.") % (record.name, record.project_id.name),
                    title=_("Job Order Created")
                )
            if record.project_id.project_owner_id:
                record.send_in_app_notification(
                    record.project_id.project_owner_id,
                    _("New Job Order '%s' has been created for project '%s'.") % (record.name, record.project_id.name),
                    title=_("Job Order Created")
                )
            # Automatically create a draft cost estimation (BOQ) for the new job order
            self.env['construction.estimate'].create({
                'project_id': record.project_id.id,
                'job_order_id': record.id,
                'state': 'draft'
            })
        return records

    def write(self, vals):
        # NOTIFICATION: Job Order Done/Closed
        if 'state' in vals:
            for record in self:
                if vals['state'] in ['completed', 'closed'] and record.state not in ['completed', 'closed']:
                    msg = _("Job Order '%s' for project '%s' has been marked as %s.") % (record.name, record.project_id.name, vals['state'].upper())
                    if record.project_id.user_id:
                        record.send_in_app_notification(record.project_id.user_id, msg, title=_("Job Order Status Change"))
                    if record.project_id.project_owner_id:
                        record.send_in_app_notification(record.project_id.project_owner_id, msg, title=_("Job Order Status Change"))
        
        return super(JobOrder, self).write(vals)

class JobMaterialLine(models.Model):
    _name = 'construction.job.material.line'
    _description = 'Job Material line'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Char(string='Description', related='product_id.name')
    quantity = fields.Float(string='Quantity', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='UOM', related='product_id.uom_id')
    cost = fields.Monetary(string='Total Cost', compute='_compute_cost')
    currency_id = fields.Many2one('res.currency', related='job_order_id.currency_id')
    consumption = fields.Float(string='Consumption', compute='_compute_consumption', store=True)
    is_consumed = fields.Boolean(string='Is Consumed', default=False)
    cost_line_id = fields.Many2one('construction.cost.material.line', string='Budget Line')
    unit_price = fields.Float(string='Unit Price')
    provided_by = fields.Selection([('contractor', 'Contractor'), ('owner', 'Owner')], string='Provided By', default='contractor')

    @api.depends('quantity', 'product_id.standard_price', 'unit_price')
    def _compute_cost(self):
        for line in self:
            price = line.unit_price or line.product_id.standard_price
            line.cost = line.quantity * price

    @api.depends("job_order_id.daily_log_ids.consumption_ids.quantity", "job_order_id.daily_log_ids.consumption_ids.product_id")
    def _compute_consumption(self):
        for line in self:
            consumption_lines = self.env["construction.job.consumption.line"].search([
                ("job_order_id", "=", line.job_order_id.id),
                ("product_id", "=", line.product_id.id),
            ])
            line.consumption = sum(consumption_lines.mapped("quantity"))

class JobConsumptionLine(models.Model):
    _name = 'construction.job.consumption.line'
    _description = 'Job Material Consumption'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order', related='daily_log_id.job_order_id', store=True, ondelete='cascade')
    daily_log_id = fields.Many2one('construction.daily.log', string='Daily Log')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Char(string='Description', related='product_id.name')
    quantity = fields.Float(string='Quantity', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='UOM', related='product_id.uom_id')
    unit_price = fields.Float(string='Unit Price')
    cost = fields.Monetary(string='Total Cost', compute='_compute_cost')
    currency_id = fields.Many2one('res.currency', related='job_order_id.currency_id')

    @api.depends('quantity', 'product_id.standard_price', 'unit_price')
    def _compute_cost(self):
        for line in self:
            price = line.unit_price or line.product_id.standard_price
            line.cost = line.quantity * price

    @api.depends("job_order_id.daily_log_ids.consumption_ids.quantity", "job_order_id.daily_log_ids.consumption_ids.product_id")
    def _compute_consumed_qty(self):
        for line in self:
            consumption_lines = self.env["construction.job.consumption.line"].search([
                ("job_order_id", "=", line.job_order_id.id),
                ("product_id", "=", line.product_id.id),
            ])
            line.consumed_qty = sum(consumption_lines.mapped("quantity"))

class JobResourceLine(models.Model):
    _name = 'construction.job.resource.line'
    _description = 'Job Resource line'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    resource_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('expense', 'Expense'),
        ('labor', 'Labor'),
        ('overhead', 'Overhead')
    ], string='Type', required=True)
    name = fields.Char(string='Resource Name/Reference', required=True)
    unit = fields.Selection([('hour', 'Hours'), ('day', 'Days'), ('unit', 'Units')], string='Unit', default='hour')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_cost = fields.Float(string='Unit Cost (Agreed)')
    total_cost = fields.Float(string='Total Cost', compute='_compute_total')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    cost_line_id = fields.Integer(string='Budget Line ID')
    cost_line_type = fields.Char(string='Budget Line Model')
    provided_by = fields.Selection([('contractor', 'Contractor'), ('owner', 'Owner')], string='Provided By', default='contractor')
    
    actual_amount = fields.Monetary(string='Actual Spent', compute='_compute_actual_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='job_order_id.currency_id')
    expense_ids = fields.One2many('construction.site.expense', 'overhead_line_id', string='Actual Expenses')

    @api.depends('expense_ids.amount', 'expense_ids.state')
    def _compute_actual_amount(self):
        for line in self:
            approved_expenses = line.expense_ids.filtered(lambda e: e.state == 'approved')
            line.actual_amount = sum(approved_expenses.mapped('amount'))

    @api.depends('quantity', 'unit_cost')
    def _compute_total(self):
        for line in self:
            line.total_cost = line.quantity * line.unit_cost

class JobChecklistLine(models.Model):
    _name = 'construction.job.checklist.line'
    _description = 'Job Quality Checklist'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order', ondelete='cascade')
    name = fields.Char(string='Instruction', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    mandatory = fields.Boolean(string='Mandatory', default=True)
    is_done = fields.Boolean(string='Completed', default=False)
    verified_by = fields.Many2one('res.users', string='Verified By')
    evidence_link = fields.Char(string='Evidence/Photo Link')

class JobMilestone(models.Model):
    _name = 'construction.job.milestone'
    _description = 'Job Order Milestone'
    _order = 'sequence, id'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order', ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    milestone_type = fields.Selection([
        ('work', 'Work Section'),
        ('payment', 'Payment Milestone')
    ], string='Type', default='work')
    name = fields.Char(string='Milestone Name', required=True)
    description = fields.Html(string='Work Description', required=True)
    percentage = fields.Float(string='Weightage (%)', help="Progress impact of this milestone")
    amount = fields.Monetary(string='Payable (Legacy)', compute='_compute_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='job_order_id.currency_id')
    
    checklist_ids = fields.Many2many('construction.job.checklist.line', string='Specific Checklists', 
                                    help="Items from the overall job checklist required for this milestone")

    state = fields.Selection([
        ('pending', 'Pending Work'),
        ('in_progress', 'Started'),
        ('inspection', 'Waiting Inspection'),
        ('approved', 'Approved')
    ], string='Status', default='pending', tracking=True)
    
    invoice_id = fields.Many2one('account.move', string='Vendor Bill (Legacy)')

    def action_create_inspection(self, remarks=False):
        self.ensure_one()
        # Ensure we don't double trigger
        if self.state != 'in_progress':
            return False
            
        inspection_vals = {
            'name': _("Inspection: %s - %s") % (self.job_order_id.name, self.name),
            'job_order_id': self.job_order_id.id,
            'milestone_id': self.id,
            'state': 'draft',
            'is_requested': True,
            'is_submitted': False,
            'contractor_remarks': remarks,
            'access_token': str(uuid.uuid4()),
        }
        
        # Set inspector from job order or project
        inspector = self.job_order_id.inspector_id or self.job_order_id.project_id.inspector_id
        if inspector:
            inspection_vals['inspector_id'] = inspector.id

        inspection = self.env['construction.inspection'].create(inspection_vals)
        
        # Populate checklist lines
        checklist_lines = self.checklist_ids or self.job_order_id.checklist_ids
        for line in checklist_lines:
            self.env['construction.inspection.line'].create({
                'inspection_id': inspection.id,
                'checklist_line_id': line.id,
                'status': 'pass', # Default for contractor to verify
            })
            
        # Send Email Template
        template = self.env.ref('construction_erp.email_template_quality_inspection_request', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(inspection.id, force_send=True)

        self.write({'state': 'inspection'})
        return inspection

class JobPayment(models.Model):
    _name = 'construction.job.payment'
    _description = 'Job Order Payment Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    job_order_id = fields.Many2one('construction.job.order', string='Job Order', ondelete='cascade')
    name = fields.Char(string='Payment Reference', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='job_order_id.currency_id')
    payment_type = fields.Selection([
        ('advance', 'Advance/Mobilization'),
        ('progress', 'Progress Claim'),
        ('final', 'Final Payment'),
        ('retention', 'Retention Release')
    ], string='Type', default='progress')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('authorized', 'Authorized'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    invoice_id = fields.Many2one('account.move', string='Related Invoice', domain="[('move_type', '=', 'out_invoice')]")
    notes = fields.Text(string='Notes')


    @api.depends('percentage', 'job_order_id.total_cost')
    def _compute_amount(self):
        for line in self:
            line.amount = (line.percentage / 100.0) * line.job_order_id.total_cost if line.job_order_id else 0.0

    @api.constrains('checklist_ids')
    def _check_checklists(self):
        for rec in self:
            if rec.state != 'pending' and not rec.checklist_ids:
                pass # Allow for now but could be enforced later

    def unlink(self):
        for rec in self:
            if rec.state in ['approved', 'billed']:
                raise UserError("You cannot delete an approved or billed milestone.")
        
        job_orders = self.mapped('job_order_id')
        res = super(JobMilestone, self).unlink()
        
        # Resequence after deletion
        for job in job_orders:
            job._resequence_milestones()
        return res

    def action_generate_bill(self):
        for ms in self:
            if ms.state == 'approved' and not ms.invoice_id:
                job = ms.job_order_id
                pct = ms.percentage / 100.0
                invoice_lines = []
                
                # Check for analytic account propagation
                analytic_distribution = {str(job.project_id.analytic_account_id.id): 100.0} if job.project_id.analytic_account_id else False

                # Pick a safe default expense account if product/category one is missing
                default_expense_account = self.env['account.account'].search([
                    ('account_type', '=', 'expense'),
                    ('company_id', '=', job.project_id.company_id.id)
                ], limit=1)

                # 1. Materials (Only if Full Contract)
                if job.contract_type == 'full':
                    for line in job.material_plan_ids:
                        # Logic: Fetch Expense account from product/category
                        product = line.product_id
                        account = product.property_account_expense_id or product.categ_id.property_account_expense_categ_id
                        if not account:
                            account = default_expense_account
                            
                        # Logic: Accurate Price Calculation with fallback to standard price
                        price_basis = line.unit_price or product.standard_price
                        
                        invoice_lines.append((0, 0, {
                            'name': f"[Material] {product.name} ({ms.percentage}% Advance)",
                            'product_id': product.id,
                            'quantity': line.quantity,
                            'price_unit': price_basis * pct,
                            'account_id': account.id if account else False,
                            'analytic_distribution': analytic_distribution,
                        }))
                
                # 2. Resources (Fleet, Equipment, Labor, Overhead)
                resource_groups = [
                    (job.vehicle_line_ids, 'Fleet'),
                    (job.equipment_line_ids, 'Equipment'),
                    (job.labor_budget_line_ids, 'Labor'),
                    (job.overhead_budget_line_ids, 'Overhead')
                ]
                for lines, label in resource_groups:
                    # Skip Overhead if not a Full Contract (Owner provided)
                    if label == 'Overhead' and job.contract_type != 'full':
                        continue
                        
                    for line in lines:
                        # Logic: Resource lines often lack product_id, using company expense fallback
                        account = default_expense_account
                        
                        # Logic: Pull agreed rate, fallback to linked budget line if 0 to ensure accuracy
                        price_basis = line.unit_cost
                        if not price_basis and line.cost_line_type and line.cost_line_id:
                            try:
                                budget_line = self.env[line.cost_line_type].browse(line.cost_line_id)
                                if budget_line.exists():
                                    price_basis = budget_line.cost_unit
                            except:
                                pass 

                        invoice_lines.append((0, 0, {
                            'name': f"[{label}] {line.name} ({ms.percentage}% Advance)",
                            'quantity': line.quantity,
                            'price_unit': price_basis * pct,
                            'account_id': account.id if account else False,
                            'analytic_distribution': analytic_distribution,
                        }))

                # Fallback if no detailed lines exist
                if not invoice_lines:
                    invoice_lines.append((0, 0, {
                        'name': ms.job_order_id.name + " - " + ms.name,
                        'quantity': 1,
                        'price_unit': ms.amount,
                        'account_id': default_expense_account.id if default_expense_account else False,
                        'analytic_distribution': analytic_distribution,
                    }))

                move = self.env['account.move'].create({
                    'move_type': 'in_invoice',
                    'partner_id': job.contractor_id.id,
                    'job_order_id': job.id,
                    'project_id': job.project_id.id,
                    'invoice_date': fields.Date.context_today(self),
                    'invoice_line_ids': invoice_lines
                })
                ms.invoice_id = move.id
                ms.state = 'billed'
