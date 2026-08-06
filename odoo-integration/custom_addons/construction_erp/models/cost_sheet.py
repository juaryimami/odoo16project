# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionCostSheet(models.Model):
    _name = 'construction.cost.sheet'
    _description = 'Job Cost Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Cost Sheet Ref', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', related='project_id.analytic_account_id', store=True)
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    partner_id = fields.Many2one('res.partner', string='Customer', related='project_id.partner_id', store=True)
    description = fields.Html(string='Description')
    
    create_date = fields.Date(string='Create Date', default=fields.Date.context_today)
    closed_date = fields.Date(string='Closed Date', readonly=True)
    
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('done', 'Done')
    ], string='Status', default='draft', tracking=True)

    # Base Line (for historical data or unified tracking if needed)
    line_ids = fields.One2many('construction.cost.sheet.line', 'cost_sheet_id', string='Legacy Lines')

    # Specialized Category Lines
    material_line_ids = fields.One2many('construction.cost.material.line', 'cost_sheet_id', string='Material Lines')
    labor_line_ids = fields.One2many('construction.cost.labor.line', 'cost_sheet_id', string='Labor Lines')
    equipment_line_ids = fields.One2many('construction.cost.equipment.line', 'cost_sheet_id', string='Equipment Lines')
    vehicle_line_ids = fields.One2many('construction.cost.vehicle.line', 'cost_sheet_id', string='Vehicle Lines')
    overhead_line_ids = fields.One2many('construction.cost.overhead.line', 'cost_sheet_id', string='Overhead Lines')

    # Financial Comparison Summary
    total_budget_amount = fields.Monetary(string='Project Budget', compute='_compute_financial_summary')
    total_actual_cost = fields.Monetary(string='Total Actual Spent', compute='_compute_financial_summary')
    total_variance_amount = fields.Monetary(string='Over/Under Budget', compute='_compute_financial_summary')
    budget_utilization_percent = fields.Float(string='Utilization (%)', compute='_compute_financial_summary')
    
    # Granular Category Sums
    material_budget_total = fields.Monetary(string='Total Material', compute='_compute_budget_totals')
    labor_budget_total = fields.Monetary(string='Total Labor', compute='_compute_budget_totals')
    overhead_budget_total = fields.Monetary(string='Total Overhead', compute='_compute_budget_totals')
    vehicle_budget_total = fields.Monetary(string='Total Vehicle', compute='_compute_budget_totals')
    equipment_budget_total = fields.Monetary(string='Total Equipment', compute='_compute_budget_totals')
    maintenance_budget_total = fields.Monetary(string='Total Maintenance', compute='_compute_budget_totals')
    total_cost = fields.Monetary(string='Total Budgeted Project Cost', compute='_compute_budget_totals')

    @api.depends('material_line_ids.subtotal', 'labor_line_ids.subtotal', 'equipment_line_ids.subtotal', 
                 'vehicle_line_ids.subtotal', 'overhead_line_ids.subtotal')
    def _compute_budget_totals(self):
        for sheet in self:
            material = sum(sheet.material_line_ids.mapped('subtotal'))
            labor = sum(sheet.labor_line_ids.mapped('subtotal'))
            equipment = sum(sheet.equipment_line_ids.mapped('subtotal'))
            vehicle = sum(sheet.vehicle_line_ids.mapped('subtotal'))
            overhead = sum(sheet.overhead_line_ids.mapped('subtotal'))
            
            sheet.material_budget_total = material
            sheet.labor_budget_total = labor
            sheet.equipment_budget_total = equipment
            sheet.vehicle_budget_total = vehicle
            sheet.overhead_budget_total = overhead
            sheet.maintenance_budget_total = 0.0
            sheet.total_cost = material + labor + equipment + vehicle + overhead

    @api.depends('total_cost', 'material_line_ids.actual_amount_spent', 'labor_line_ids.actual_amount_spent',
                 'equipment_line_ids.actual_amount_spent', 'vehicle_line_ids.actual_amount_spent', 'overhead_line_ids.actual_amount_spent')
    def _compute_financial_summary(self):
        for sheet in self:
            budget = sheet.total_cost
            actual = sum(sheet.material_line_ids.mapped('actual_amount_spent')) + \
                     sum(sheet.labor_line_ids.mapped('actual_amount_spent')) + \
                     sum(sheet.equipment_line_ids.mapped('actual_amount_spent')) + \
                     sum(sheet.vehicle_line_ids.mapped('actual_amount_spent')) + \
                     sum(sheet.overhead_line_ids.mapped('actual_amount_spent'))
            
            sheet.total_budget_amount = budget
            sheet.total_actual_cost = actual
            sheet.total_variance_amount = budget - actual
            sheet.budget_utilization_percent = (actual / budget * 100) if budget else 0.0

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Orders'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'default_project_id': self.project_id.id},
        }

    def action_view_vendor_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.project_id.id), ('move_type', '=', 'in_invoice')],
            'context': {'default_project_id': self.project_id.id, 'default_move_type': 'in_invoice'},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.cost.sheet') or _('New')
        return super(ConstructionCostSheet, self).create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_done(self):
        self.write({'state': 'done', 'closed_date': fields.Date.context_today(self)})

# --- Base Abstract Model for shared behavior ---
class ConstructionCostBaseLine(models.AbstractModel):
    _name = 'construction.cost.base.line'
    _description = 'Abstract Cost Line'

    cost_sheet_id = fields.Many2one('construction.cost.sheet', string='Cost Sheet')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Planned Qty/Unit', default=1.0)
    cost_unit = fields.Float(string='Unit Cost')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one('res.currency', related='cost_sheet_id.currency_id')

    actual_amount_spent = fields.Monetary(string='Money Spent', compute='_compute_actuals')
    variance_amount = fields.Monetary(string='Variance', compute='_compute_variance')

    # Variation tracking
    is_variation = fields.Boolean(string='Is Variation', default=False)
    variation_id = fields.Many2one('construction.variation.order', string='Variation Order')

    @api.depends('quantity', 'cost_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.cost_unit

    def _compute_actuals(self):
        for line in self:
            actual_spend = 0.0
            # 1. External Spend (Vendor Bills & Direct Linking)
            domain = [
                ('parent_state', '=', 'posted'),
                ('move_id.payment_state', 'in', ['paid', 'in_payment']),
                ('move_id.job_order_id', '=', line.cost_sheet_id.job_order_id.id),
                ('cost_line_id_ref', '=', f"{self._name},{line.id}")
            ]
            
            # Material-Specific Procurement Fallback (PO -> Job Material -> Master Material)
            if self._name == 'construction.cost.material.line':
                domain = [
                    ('parent_state', '=', 'posted'),
                    ('move_id.payment_state', 'in', ['paid', 'in_payment']),
                    ('move_id.job_order_id', '=', line.cost_sheet_id.job_order_id.id),
                    '|',
                    ('cost_line_id_ref', '=', f"{self._name},{line.id}"),
                    ('purchase_line_id.cost_line_id.cost_line_id', '=', line.id)
                ]

            inv_lines = self.env['account.move.line'].search(domain)
            actual_spend += sum(inv_lines.mapped('price_subtotal'))
            
            # 2. Internal Spend (Job Order Consumption)
            if self._name == 'construction.cost.material.line':
                consumed = self.env['construction.job.material.line'].search([
                    ('cost_line_id', '=', line.id),
                    ('is_consumed', '=', True)
                ])
                actual_spend += sum(consumed.mapped('cost'))
            elif self._name in ['construction.cost.equipment.line', 'construction.cost.vehicle.line', 'construction.cost.labor.line']:
                # Equipment, Fleet, and Labor are purely tracked via contractor payments (Vendor Bills) in Section 1.
                # All internal timesheets and incidental site expenses are excluded to maintain contractor-led isolation.
                pass
            elif self._name == 'construction.cost.overhead.line':
                # Rollup PAID site expenses from JO lines
                jo_lines = self.env['construction.job.resource.line'].search([
                    ('cost_line_id', '=', line.id),
                    ('cost_line_type', '=', 'construction.cost.overhead.line'),
                    ('job_order_id', '=', line.cost_sheet_id.job_order_id.id)
                ])
                if jo_lines:
                    # Find bills linked to these JOB lines that are PAID
                    ref_keys = [f"construction.job.resource.line,{jo.id}" for jo in jo_lines]
                    paid_expenses = self.env['account.move.line'].search([
                        ('cost_line_id_ref', 'in', ref_keys),
                        ('parent_state', '=', 'posted'),
                        ('move_id.payment_state', 'in', ['paid', 'in_payment']),
                        ('move_id.job_order_id', '=', line.cost_sheet_id.job_order_id.id)
                    ])
                    actual_spend += sum(paid_expenses.mapped('price_subtotal'))

            line.actual_amount_spent = actual_spend

    @api.depends('subtotal', 'actual_amount_spent')
    def _compute_variance(self):
        for line in self:
            line.variance_amount = line.subtotal - line.actual_amount_spent

    def unlink(self):
        from odoo.exceptions import UserError
        for line in self:
            if line.cost_sheet_id.state != 'draft':
                raise UserError(_("You can only delete budget lines when the Cost Sheet is in the Draft state."))
        return super(ConstructionCostBaseLine, self).unlink()

    def action_view_actual_details(self):
        """ Opens a view showing the granular documents contributing to Actual Spent. """
        self.ensure_one()
        
        # Determine specialized view for overhead
        if self._name == 'construction.cost.overhead.line':
            return {
                'name': _('Site Expenses: %s') % (self.description or ''),
                'type': 'ir.actions.act_window',
                'res_model': 'construction.site.expense',
                'view_mode': 'tree,form',
                'domain': [
                    ('overhead_line_id.cost_line_id', '=', self.id),
                    ('overhead_line_id.cost_line_type', '=', 'construction.cost.overhead.line'),
                    ('job_order_id', '=', self.cost_sheet_id.job_order_id.id)
                ],
                'context': {'create': False, 'edit': False, 'delete': False},
                'target': 'new',
            }
        
        # General view for Material, Labor, Equipment, Vehicle (Vendor Invoice Lines)
        domain = [
            ('parent_state', '=', 'posted'),
            ('move_id.payment_state', 'in', ['paid', 'in_payment']),
            ('move_id.job_order_id', '=', self.cost_sheet_id.job_order_id.id),
            ('cost_line_id_ref', '=', f"{self._name},{self.id}")
        ]

        if self._name == 'construction.cost.material.line':
            domain = [
                ('parent_state', '=', 'posted'),
                ('move_id.payment_state', 'in', ['paid', 'in_payment']),
                ('move_id.job_order_id', '=', self.cost_sheet_id.job_order_id.id),
                '|',
                ('cost_line_id_ref', '=', f"{self._name},{self.id}"),
                ('purchase_line_id.cost_line_id.cost_line_id', '=', self.id)
            ]
        elif self._name == 'construction.cost.overhead.line':
            jo_lines = self.env['construction.job.resource.line'].search([
                ('cost_line_id', '=', self.id),
                ('cost_line_type', '=', 'construction.cost.overhead.line'),
                ('job_order_id', '=', self.cost_sheet_id.job_order_id.id)
            ])
            ref_keys = [f"construction.job.resource.line,{jo.id}" for jo in jo_lines]
            domain = [
                ('parent_state', '=', 'posted'),
                ('move_id.payment_state', 'in', ['paid', 'in_payment']),
                ('move_id.job_order_id', '=', self.cost_sheet_id.job_order_id.id),
                ('cost_line_id_ref', 'in', ref_keys)
            ]

        return {
            'name': _('Financial Documents: %s') % (self.description or ''),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False, 'edit': False, 'delete': False},
            'target': 'new',
        }

# --- Specialized Models ---

class ConstructionCostMaterialLine(models.Model):
    _name = 'construction.cost.material.line'
    _inherit = 'construction.cost.base.line'
    _description = 'Material Budget Line'

    product_id = fields.Many2one('product.product', string='Material', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit', related='product_id.uom_id')
    procurement_lead_time = fields.Integer(string='Procurement Lead Time (Days)', default=0)
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.cost_unit = self.product_id.standard_price

class ConstructionCostLaborLine(models.Model):
    _name = 'construction.cost.labor.line'
    _inherit = 'construction.cost.base.line'
    _description = 'Labor Budget Line'

    role_id = fields.Many2one('res.partner.category', string='Role/Expertise')
    employee_count = fields.Integer(string='No. of Persons', default=1)
    hours_per_person = fields.Float(string='Hours/Person')
    
    @api.depends('employee_count', 'hours_per_person', 'cost_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.employee_count * line.hours_per_person * line.cost_unit

class ConstructionCostEquipmentLine(models.Model):
    _name = 'construction.cost.equipment.line'
    _inherit = 'construction.cost.base.line'
    _description = 'Equipment Budget Line'

    equipment_id = fields.Many2one('product.product', string='Equipment/Machine', domain=[('type', '=', 'service')])
    rate_type = fields.Selection([('hourly', 'Hourly'), ('daily', 'Daily')], default='hourly')

class ConstructionCostVehicleLine(models.Model):
    _name = 'construction.cost.vehicle.line'
    _inherit = 'construction.cost.base.line'
    _description = 'Vehicle Budget Line'

    vehicle_id = fields.Many2one('product.product', string='Vehicle/Truck')

class ConstructionCostOverheadLine(models.Model):
    _name = 'construction.cost.overhead.line'
    _inherit = 'construction.cost.base.line'
    _description = 'Overhead Budget Line'

# Legacy model keeping for safety during migration
class ConstructionCostSheetLine(models.Model):
    _name = 'construction.cost.sheet.line'
    _description = 'Legacy Cost Sheet Line'
    cost_sheet_id = fields.Many2one('construction.cost.sheet')
    cost_type = fields.Selection([('material', 'Material'), ('labor', 'Labor'), ('overhead', 'Overhead')])
    product_id = fields.Many2one('product.product')
    subtotal = fields.Float()
    actual_amount_spent = fields.Float()
