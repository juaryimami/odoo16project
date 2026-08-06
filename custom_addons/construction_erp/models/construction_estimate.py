# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionEstimate(models.Model):
    _name = 'construction.estimate'
    _description = 'Bill of Quantities / Estimate'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']

    name = fields.Char(string='Estimate Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    job_order_id = fields.Many2one('construction.job.order', string='Associated Job Order', domain="[('project_id', '=', project_id)]")
    date = fields.Date(string='Date', default=fields.Date.context_today)
    total_estimated_amount = fields.Monetary(string='Total Estimated', compute='_compute_total', store=True, tracking=True)
    total_material = fields.Monetary(string='Total Material', compute='_compute_total', store=True)
    total_labor = fields.Monetary(string='Total Labor', compute='_compute_total', store=True)
    total_equipment = fields.Monetary(string='Total Equipment', compute='_compute_total', store=True)
    total_vehicle = fields.Monetary(string='Total Fleet', compute='_compute_total', store=True)
    total_overhead = fields.Monetary(string='Total Overhead', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Pending PM Approval'),
        ('pm_approved', 'Pending Owner Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    cost_sheet_id = fields.Many2one('construction.cost.sheet', string='Main Cost Sheet', readonly=True)
    line_ids = fields.One2many('construction.estimate.line', 'estimate_id', string='Estimate Lines')
    
    # Filtered lines for multi-tab UI
    material_line_ids = fields.One2many('construction.estimate.line', 'estimate_id', string='Material Lines', domain=[('type', '=', 'material')])
    labor_line_ids = fields.One2many('construction.estimate.line', 'estimate_id', string='Labor Lines', domain=[('type', '=', 'labor')])
    equipment_line_ids = fields.One2many('construction.estimate.line', 'estimate_id', string='Equipment Lines', domain=[('type', '=', 'equipment')])
    vehicle_line_ids = fields.One2many('construction.estimate.line', 'estimate_id', string='Fleet Lines', domain=[('type', '=', 'vehicle')])
    overhead_line_ids = fields.One2many('construction.estimate.line', 'estimate_id', string='Overhead Lines', domain=[('type', '=', 'overhead')])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.estimate') or _('New')
        return super(ConstructionEstimate, self).create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})
        # NOTIFICATION: Submitted for PM Approval
        if self.project_id.user_id:
            self.send_in_app_notification(
                self.project_id.user_id,
                _("Cost Estimation '%s' has been submitted for your review.") % self.name,
                title=_("Budget Approval Required")
            )

    def action_approve(self):
        """ PM Level Approval """
        self.write({'state': 'pm_approved'})
        
        # Notify Owner (In-app)
        owner = self.project_id.project_owner_id
        if owner:
            msg = _("Cost Estimation %s has been approved by PM and requires your final sign-off.") % self.name
            self.send_in_app_notification(owner, msg, title=_("Budget Approval Required"))
            self.notify_contact(owner.partner_id, msg, title=_("Budget Approval Required"))

    def action_owner_approve(self):
        """ Owner Level Approval """
        self.write({'state': 'approved'})
        # Notify PM of final approval
        if self.project_id.user_id:
            self.send_in_app_notification(
                self.project_id.user_id,
                _("Cost Estimation '%s' has received final approval from the Project Owner.") % self.name,
                title=_("Budget Finalized")
            )

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_import_excel(self):
        self.ensure_one()
        return {
            'name': _('Import Budget Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.estimate.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_estimate_id': self.id}
        }

    def action_create_cost_sheet(self):
        self.ensure_one()
        from odoo.exceptions import UserError
        if self.state != 'approved':
            raise UserError(_("Only approved estimates can be converted to a budget."))
        
        if self.cost_sheet_id:
            raise UserError(_("This estimate has already been converted to a budget: %s") % self.cost_sheet_id.name)
        
        # Create or find master cost sheet for the project and job order
        domain = [('project_id', '=', self.project_id.id)]
        if self.job_order_id:
            domain.append(('job_order_id', '=', self.job_order_id.id))
            
        cost_sheet = self.env['construction.cost.sheet'].search(domain, limit=1)
        if not cost_sheet:
            cs_name = self.project_id.name
            if self.job_order_id:
                cs_name = f"{cs_name} - {self.job_order_id.name}"
            else:
                cs_name = f"Budget for {cs_name}"
                
            cost_sheet = self.env['construction.cost.sheet'].create({
                'project_id': self.project_id.id,
                'job_order_id': self.job_order_id.id if self.job_order_id else False,
                'name': cs_name,
            })
        
        # Build lines properly grouped by specialized category
        cost_vals = {
            'material_line_ids': [],
            'labor_line_ids': [],
            'equipment_line_ids': [],
            'vehicle_line_ids': [],
            'overhead_line_ids': [],
        }
        
        for line in self.line_ids:
            # Base logic for all lines
            vals = {
                'description': line.product_id.name,
                'quantity': line.quantity,
                'cost_unit': line.unit_price,
                'phase_id': self.job_order_id.phase_id.id if self.job_order_id else False,
                'job_order_id': self.job_order_id.id if self.job_order_id else False,
            }
            
            if line.type == 'material':
                vals['product_id'] = line.product_id.id
                cost_vals['material_line_ids'].append((0, 0, vals))
            elif line.type == 'labor':
                # Labor does not use product_id
                vals.update({
                    'hours_per_person': line.quantity,
                    'employee_count': 1,
                })
                cost_vals['labor_line_ids'].append((0, 0, vals))
            elif line.type == 'equipment':
                # Equipment uses equipment_id
                vals['equipment_id'] = line.product_id.id
                cost_vals['equipment_line_ids'].append((0, 0, vals))
            elif line.type == 'vehicle':
                # Vehicle uses vehicle_id
                vals['vehicle_id'] = line.product_id.id
                cost_vals['vehicle_line_ids'].append((0, 0, vals))
            elif line.type == 'overhead':
                # Overhead does not use product_id
                cost_vals['overhead_line_ids'].append((0, 0, vals))
            else:
                vals['product_id'] = line.product_id.id
                cost_vals['material_line_ids'].append((0, 0, vals))
        
        cost_sheet.write(cost_vals)
        self.cost_sheet_id = cost_sheet.id
        self.job_order_id.cost_sheet_id = cost_sheet.id
        
        # NOTIFICATION: Cost Sheet Created
        msg = _("A master Project Budget (Cost Sheet) has been initialized for project '%s' based on estimation %s.") % (self.project_id.name, self.name)
        if self.project_id.user_id:
            self.send_in_app_notification(self.project_id.user_id, msg, title=_("Budget Initialized"))
        if self.project_id.project_owner_id:
            self.send_in_app_notification(self.project_id.project_owner_id, msg, title=_("Budget Initialized"))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'construction.cost.sheet',
            'res_id': cost_sheet.id,
            'view_mode': 'form',
        }

    def action_view_cost_sheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'construction.cost.sheet',
            'res_id': self.cost_sheet_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.depends('line_ids.subtotal', 'line_ids.type')
    def _compute_total(self):
        for record in self:
            material = sum(line.subtotal for line in record.line_ids if line.type == 'material')
            labor = sum(line.subtotal for line in record.line_ids if line.type == 'labor')
            equipment = sum(line.subtotal for line in record.line_ids if line.type == 'equipment')
            vehicle = sum(line.subtotal for line in record.line_ids if line.type == 'vehicle')
            overhead = sum(line.subtotal for line in record.line_ids if line.type == 'overhead')
            
            record.total_material = material
            record.total_labor = labor
            record.total_equipment = equipment
            record.total_vehicle = vehicle
            record.total_overhead = overhead
            record.total_estimated_amount = material + labor + equipment + vehicle + overhead

class ConstructionEstimateLine(models.Model):
    _name = 'construction.estimate.line'
    _description = 'Estimate Line'

    estimate_id = fields.Many2one('construction.estimate', string='Estimate Reference')
    product_id = fields.Many2one('product.product', string='Product / Service', required=True)
    type = fields.Selection([
        ('material', 'Material'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment'),
        ('vehicle', 'Vehicle / Fleet'),
        ('overhead', 'Overhead & Admin')
    ], string='Item Type', default='material')
    quantity = fields.Float(string='Estimated Qty', default=1.0)
    quantity_consumed = fields.Float(string='Consumed Qty', compute='_compute_consumption')
    quantity_variance = fields.Float(string='Variance', compute='_compute_consumption')
    consumption_percentage = fields.Float(string='Consumption (%)', compute='_compute_consumption')
    unit_price = fields.Float(string='Unit Price')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'estimate_id.project_id')
    def _compute_consumption(self):
        for line in self:
            consumed = 0.0
            if line.type == 'material' and line.product_id and line.estimate_id.project_id:
                consumptions = self.env['construction.consumption.line'].search([
                    ('consumption_id.project_id', '=', line.estimate_id.project_id.id),
                    ('consumption_id.state', '=', 'validated'),
                    ('product_id', '=', line.product_id.id)
                ])
                consumed = sum(consumptions.mapped('quantity'))
            
            line.quantity_consumed = consumed
            line.quantity_variance = line.quantity - consumed
            line.consumption_percentage = (consumed / line.quantity * 100) if line.quantity else 0.0

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    def unlink(self):
        from odoo.exceptions import UserError
        for line in self:
            if line.estimate_id.state != 'draft':
                raise UserError(_("You can only delete estimation lines when the BOQ is in the Draft state."))
        return super(ConstructionEstimateLine, self).unlink()
