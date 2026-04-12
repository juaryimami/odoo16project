# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionEstimate(models.Model):
    _name = 'construction.estimate'
    _description = 'Bill of Quantities / Estimate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Estimate Reference', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    task_id = fields.Many2one('project.task', string='Phase / Task', domain="[('project_id', '=', project_id)]")
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
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    cost_sheet_id = fields.Many2one('construction.cost.sheet', string='Main Cost Sheet', readonly=True)
    line_ids = fields.One2many('construction.estimate.line', 'estimate_id', string='Estimate Lines')

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_create_cost_sheet(self):
        self.ensure_one()
        from odoo.exceptions import UserError
        if self.state != 'approved':
            raise UserError(_("Only approved estimates can be converted to a budget."))
        
        if self.cost_sheet_id:
            raise UserError(_("This estimate has already been converted to a budget: %s") % self.cost_sheet_id.name)
        
        # Create or find master cost sheet for the project
        cost_sheet = self.env['construction.cost.sheet'].search([('project_id', '=', self.project_id.id)], limit=1)
        if not cost_sheet:
            cost_sheet = self.env['construction.cost.sheet'].create({
                'project_id': self.project_id.id,
                'name': f"Budget for {self.project_id.name}",
            })
        
        # Build lines properly grouped by phase
        new_lines = []
        for line in self.line_ids:
            # Map estimate types to cost sheet types
            type_map = {
                'material': 'material',
                'labor': 'labor',
                'equipment': 'equipment',
                'vehicle': 'vehicle',
                'overhead': 'overhead'
            }
            new_lines.append((0, 0, {
                'cost_type': type_map.get(line.type, 'material'),
                'product_id': line.product_id.id,
                'description': line.product_id.name,
                'quantity': line.quantity,
                'cost_unit': line.unit_price,
                'phase_id': self.task_id.phase_id.id if self.task_id else False,
            }))
        
        cost_sheet.write({'line_ids': new_lines})
        self.cost_sheet_id = cost_sheet.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'construction.cost.sheet',
            'res_id': cost_sheet.id,
            'view_mode': 'form',
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
