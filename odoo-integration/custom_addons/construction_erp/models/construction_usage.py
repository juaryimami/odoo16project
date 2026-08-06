# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionUsageLog(models.Model):
    _name = 'construction.usage.log'
    _description = 'Site Resource Usage Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Usage Ref', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True)
    phase_id = fields.Many2one('construction.phase', string='Phase', domain="[('lifecycle_id', '=', lifecycle_id)]")
    lifecycle_id = fields.Many2one('construction.lifecycle', related='project_id.lifecycle_id', store=True)
    
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    
    resource_type = fields.Selection([
        ('vehicle', 'Vehicle / Fleet'),
        ('equipment', 'Heavy Equipment / Machinery'),
        ('labor', 'Contractor Labor / Manpower')
    ], string='Resource Category', required=True)
    
    product_id = fields.Many2one('product.product', string='Resource / Item', required=True)
    
    # Usage Metrics
    start_reading = fields.Float(string='Start Reading (Hrs/Km)')
    end_reading = fields.Float(string='End Reading (Hrs/Km)')
    quantity = fields.Float(string='Usage Quantity', compute='_compute_usage_qty', store=True)
    uom_id = fields.Many2one('uom.uom', string='UOM', related='product_id.uom_id')
    
    operator_id = fields.Many2one('res.partner', string='Operator / Supervisor')
    notes = fields.Text(string='Work Performed / Observations')
    
    # Financial Link
    cost_line_id = fields.Many2one('construction.cost.sheet.line', string='Budget Line',
                                   help="Link this usage specifically to a budget allocation")
    
    unit_cost = fields.Float(string='Standard Unit Cost', related='product_id.standard_price')
    total_cost = fields.Monetary(string='Total Usage Cost', compute='_compute_total_cost', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    @api.depends('start_reading', 'end_reading', 'resource_type')
    def _compute_usage_qty(self):
        for log in self:
            if log.resource_type in ['vehicle', 'equipment'] and log.end_reading > log.start_reading:
                log.quantity = log.end_reading - log.start_reading
            elif not log.start_reading and not log.end_reading:
                # Manual entry for labor/manpower
                pass

    @api.depends('quantity', 'unit_cost')
    def _compute_total_cost(self):
        for log in self:
            log.total_cost = log.quantity * log.unit_cost

    @api.onchange('product_id', 'project_id', 'phase_id')
    def _onchange_suggest_budget_line(self):
        if self.product_id and self.project_id:
            domain = [
                ('product_id', '=', self.product_id.id),
                ('cost_sheet_id.project_id', '=', self.project_id.id)
            ]
            if self.phase_id:
                domain.append(('phase_id', '=', self.phase_id.id))
            
            match = self.env['construction.cost.sheet.line'].search(domain, limit=1)
            if match:
                self.cost_line_id = match

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.usage.log') or _('New')
        return super(ConstructionUsageLog, self).create(vals_list)
