# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class JobOrder(models.Model):
    _name = 'construction.job.order'
    _description = 'Contractor Job Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']

    name = fields.Char(string='Job Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='project_id.partner_id', store=True)
    
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
    agreed_rate = fields.Monetary(string='Agreed Rate', currency_field='currency_id', tracking=True)
    total_cost = fields.Monetary(string='Total Cost', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
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

    # Resource Tabs
    material_plan_ids = fields.One2many('construction.job.material.line', 'job_order_id', string='Material Planning')
    material_consumed_ids = fields.One2many('construction.job.material.line', 'job_order_id', string='Consumed Materials', domain=[('is_consumed', '=', True)])
    vehicle_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Vehicles', domain=[('resource_type', '=', 'vehicle')])
    equipment_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Equipment', domain=[('resource_type', '=', 'equipment')])
    expense_line_ids = fields.One2many('construction.job.resource.line', 'job_order_id', string='Expenses', domain=[('resource_type', '=', 'expense')])
    
    checklist_ids = fields.One2many('construction.job.checklist.line', 'job_order_id', string='Checklist Items')
    extra_info = fields.Text(string='Extra Info')

    # Labor / Timesheet Integration
    timesheet_ids = fields.One2many('account.analytic.line', 'job_order_id', string='Timesheets')

    # Financial Aggregation
    total_material_cost = fields.Monetary(string='Material Cost', compute='_compute_total_costs', store=True)
    total_resource_cost = fields.Monetary(string='Resource Cost', compute='_compute_total_costs', store=True)
    total_labor_cost = fields.Monetary(string='Labor Cost', compute='_compute_total_costs', store=True)
    actual_total_cost = fields.Monetary(string='Actual Total Cost', compute='_compute_total_costs', store=True)

    @api.depends('material_consumed_ids.cost', 'vehicle_line_ids.total_cost', 'equipment_line_ids.total_cost', 'expense_line_ids.total_cost', 'timesheet_ids.amount')
    def _compute_total_costs(self):
        for record in self:
            mat_cost = sum(record.material_consumed_ids.mapped('cost'))
            res_cost = sum(record.vehicle_line_ids.mapped('total_cost')) + \
                       sum(record.equipment_line_ids.mapped('total_cost')) + \
                       sum(record.expense_line_ids.mapped('total_cost'))
            labor_cost = abs(sum(record.timesheet_ids.mapped('amount')))
            
            record.total_material_cost = mat_cost
            record.total_resource_cost = res_cost
            record.total_labor_cost = labor_cost
            record.actual_total_cost = mat_cost + res_cost + labor_cost

    # Counters
    invoice_count = fields.Integer(compute='_compute_counts')
    inspection_count = fields.Integer(compute='_compute_counts')
    requisition_count = fields.Integer(compute='_compute_counts')
    cpr_count = fields.Integer(compute='_compute_counts')
    picking_count = fields.Integer(compute='_compute_counts')
    on_hand_count = fields.Integer(compute='_compute_counts', string='On Hand Qty')

    is_inspected_passed = fields.Boolean(compute='_compute_is_passed', string='Passed Inspection')
    progress_ratio = fields.Float(compute='_compute_is_passed', string='Job Completion (%)')

    milestone_ids = fields.One2many('construction.job.milestone', 'job_order_id', string='Payment Milestones')
    
    picking_ids = fields.One2many('stock.picking', 'job_order_id', string='Stock Pickings')

    @api.depends('state', 'milestone_ids.state', 'checklist_ids.is_done')
    def _compute_is_passed(self):
        for order in self:
            if order.state in ['completed', 'closed']:
                order.is_inspected_passed = True
                order.progress_ratio = 100.0
                continue
            
            if order.milestone_ids:
                # If milestones exist, use them for progress
                approved = order.milestone_ids.filtered(lambda m: m.state in ['approved', 'billed'])
                order.progress_ratio = sum(approved.mapped('percentage'))
                order.is_inspected_passed = order.progress_ratio >= 100.0
            elif order.checklist_ids:
                # Use checklist for granular progress if milestones aren't used
                total = len(order.checklist_ids)
                done = len(order.checklist_ids.filtered(lambda c: c.is_done))
                order.progress_ratio = (done / total * 100.0) if total > 0 else 0.0
                order.is_inspected_passed = order.progress_ratio >= 100.0
            else:
                # Basic state fallback
                order.is_inspected_passed = False
                order.progress_ratio = 50.0 if order.state == 'active' else 0.0

    def _compute_counts(self):
        for order in self:
            order.requisition_count = self.env['construction.material.requisition'].search_count([('job_order_id', '=', order.id)])
            order.cpr_count = self.env['construction.cpr'].search_count([('job_order_id', '=', order.id)])
            order.inspection_count = self.env['construction.inspection'].search_count([('job_order_id', '=', order.id)])
            order.invoice_count = len(self.env['account.move'].search([('job_order_id', '=', order.id)]))
            order.picking_count = len(order.picking_ids)
            # Dummy on hand for UI consistency as per screenshot
            warehouse = order.project_id.warehouse_id
            order.on_hand_count = sum(order.material_plan_ids.mapped('product_id.qty_available')) if warehouse else 0

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
                'is_consumed': False,
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
                'unit': 'unit',
            }))

        # 3. Load Labor Plans (as notes or dedicated lines if model existed)
        labor_lines = self.env['construction.cost.labor.line'].search(mat_domain)
        if labor_lines:
            labor_summary = "\n".join([f"- {l.role_id.name or 'Labor'}: {l.employee_count} persons for {l.hours_per_person} hrs" for l in labor_lines])
            self.message_post(body=_("<b>Planned Labor Allocation:</b>\n%s") % labor_summary)

        # Update Job Order Collections
        self.write({
            'material_plan_ids': [(5, 0, 0)] + mat_vals,
            'equipment_line_ids': [(5, 0, 0)] + [v for v in res_vals if v[2]['resource_type'] == 'equipment'],
            'vehicle_line_ids': [(5, 0, 0)] + [v for v in res_vals if v[2]['resource_type'] == 'vehicle'],
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
            return
        
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
        picking = self.env['stock.picking'].create({
            'job_order_id': self.id,
            'project_id': self.project_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': self.project_id.warehouse_id.lot_stock_id.id,
            'move_ids_without_package': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': self.project_id.warehouse_id.lot_stock_id.id,
            }) for line in self.material_plan_ids]
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
        }

    def action_return_to_warehouse(self):
        self.ensure_one()
        # Create a Return picking (Internal Site -> Main Warehouse)
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
        picking = self.env['stock.picking'].create({
            'job_order_id': self.id,
            'project_id': self.project_id.id,
            'picking_type_id': picking_type.id,
            'location_id': self.project_id.warehouse_id.lot_stock_id.id,
            'location_dest_id': picking_type.default_location_src_id.id,
            'move_ids_without_package': [(0, 0, {
                'name': line.product_id.name + " (Return)",
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': self.project_id.warehouse_id.lot_stock_id.id,
                'location_dest_id': picking_type.default_location_src_id.id,
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
            'context': {'default_job_order_id': self.id},
        }

    def action_offer(self):
        for record in self:
            if not record.contractor_id:
                from odoo.exceptions import UserError
                raise UserError(_("Please select a contractor before making an offer."))
            
            record.state = 'offered'
            msg = _("Job Offer: %s Project: %s. Please review and accept via your portal.") % (record.name, record.project_id.name)
            record.notify_contact(record.contractor_id, msg, title=_("Job Offer Pending"))
            record.message_post(body=_("Contract offer sent to %s") % record.contractor_id.name)

    def action_accept(self):
        for record in self:
            record.state = 'accepted'
            record.message_post(body=_("Contract officially accepted by %s") % record.contractor_id.name)

    def action_start(self):
        for record in self:
            record.state = 'active'
            record.date_start_actual = fields.Datetime.now()
            record.message_post(body=_("Mobilization started - Work is now IN PROGRESS"))

    def action_complete(self):
        for record in self:
            record.state = 'ready_for_inspection'
            record.date_finish_actual = fields.Datetime.now()
            # AUTO-TRIGGER INSPECTION
            if record.milestone_id:
                inspection = self.env['construction.inspection'].create({
                    'name': f"Inspection for {record.name} - {record.milestone_id.name}",
                    'milestone_id': record.milestone_id.id,
                })
                record.message_post(body=_("Work reported finished. Quality Inspection %s has been auto-generated.") % inspection.name)
            else:
                record.message_post(body=_("Work reported finished. Please link a milestone to trigger formal inspection."))

    def action_rework(self):
        for record in self:
            record.state = 'rework'
            record.message_post(body=_("Inspector requested rework. Rework Required status activated."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.job.order') or _('New')
        return super(JobOrder, self).create(vals_list)

class JobMaterialLine(models.Model):
    _name = 'construction.job.material.line'
    _description = 'Job Material line'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Char(string='Description', related='product_id.name')
    quantity = fields.Float(string='Quantity', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='UOM', related='product_id.uom_id')
    cost = fields.Monetary(string='Total Cost', compute='_compute_cost', store=True)
    currency_id = fields.Many2one('res.currency', related='job_order_id.currency_id')
    is_consumed = fields.Boolean(string='Is Consumed', default=False)

    @api.depends('quantity', 'product_id.standard_price')
    def _compute_cost(self):
        for line in self:
            line.cost = line.quantity * line.product_id.standard_price

class JobResourceLine(models.Model):
    _name = 'construction.job.resource.line'
    _description = 'Job Resource line'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    resource_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('expense', 'Expense')
    ], string='Type', required=True)
    name = fields.Char(string='Resource Name/Reference', required=True)
    unit = fields.Selection([('hour', 'Hours'), ('day', 'Days'), ('unit', 'Units')], string='Unit', default='hour')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_cost = fields.Float(string='Unit Cost (Agreed)')
    total_cost = fields.Float(string='Total Cost', compute='_compute_total', store=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)

    @api.depends('quantity', 'unit_cost')
    def _compute_total(self):
        for line in self:
            line.total_cost = line.quantity * line.unit_cost

class JobChecklistLine(models.Model):
    _name = 'construction.job.checklist.line'
    _description = 'Job Quality Checklist'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    name = fields.Char(string='Instruction', required=True)
    is_done = fields.Boolean(string='Completed', default=False)
    verified_by = fields.Many2one('res.users', string='Verified By')
    evidence_link = fields.Char(string='Evidence/Photo Link')

class JobMilestone(models.Model):
    _name = 'construction.job.milestone'
    _description = 'Job Order Milestone'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    name = fields.Char(string='Milestone Phase (e.g., 20% Mobilization)', required=True)
    percentage = fields.Float(string='Percentage (%)')
    amount = fields.Monetary(string='Payable Amount', compute='_compute_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='job_order_id.currency_id')
    
    state = fields.Selection([
        ('pending', 'Pending Work'),
        ('inspection', 'Waiting Inspection'),
        ('approved', 'Approved'),
        ('billed', 'Billed')
    ], string='Status', default='pending')
    
    invoice_id = fields.Many2one('account.move', string='Vendor Bill')

    @api.depends('percentage', 'job_order_id.total_cost')
    def _compute_amount(self):
        for line in self:
            line.amount = (line.percentage / 100.0) * line.job_order_id.total_cost if line.job_order_id else 0.0

    def action_generate_bill(self):
        for ms in self:
            if ms.state == 'approved' and not ms.invoice_id:
                move = self.env['account.move'].create({
                    'move_type': 'in_invoice',
                    'partner_id': ms.job_order_id.contractor_id.id,
                    'job_order_id': ms.job_order_id.id,
                    'invoice_date': fields.Date.context_today(self),
                    'invoice_line_ids': [(0, 0, {
                        'name': ms.job_order_id.name + " - " + ms.name,
                        'quantity': 1,
                        'price_unit': ms.amount,
                        'account_id': ms.job_order_id.contractor_id.property_account_payable_id.id,
                        'analytic_distribution': {str(ms.job_order_id.project_id.analytic_account_id.id): 100} if ms.job_order_id.project_id.analytic_account_id else False,
                    })]
                })
                ms.invoice_id = move.id
                ms.state = 'billed'
