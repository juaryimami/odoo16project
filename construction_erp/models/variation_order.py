# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionVariationOrder(models.Model):
    _name = 'construction.variation.order'
    _description = 'Variation Order (V.O.)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']
    _order = 'id desc'

    name = fields.Char(string='V.O. Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True)
    estimate_id = fields.Many2one('construction.estimate', string='Original BOQ', domain="[('project_id', '=', project_id)]")
    
    date = fields.Date(string='Variation Date', default=fields.Date.context_today, required=True)
    reason = fields.Text(string='Reason for Variation', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    line_ids = fields.One2many('construction.variation.line', 'variation_id', string='Variation Lines')
    
    total_amount = fields.Monetary(string='Total Variation Amount', compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for vo in self:
            vo.total_amount = sum(vo.line_ids.mapped('subtotal'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.variation.order') or _('New')
        return super(ConstructionVariationOrder, self).create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.ensure_one()
        # Find Master Cost Sheet
        cost_sheet = self.env['construction.cost.sheet'].search([('project_id', '=', self.project_id.id)], limit=1)
        if not cost_sheet:
            from odoo.exceptions import UserError
            raise UserError(_("No Master Cost Sheet found for this project. Please initialize the project budget first."))
        
        # Inject lines into Cost Sheet
        new_lines = []
        for line in self.line_ids:
            new_lines.append((0, 0, {
                'cost_sheet_id': cost_sheet.id,
                'cost_type': line.cost_type,
                'product_id': line.product_id.id,
                'description': f"[V.O. {self.name}] {line.description or line.product_id.name}",
                'quantity': line.quantity,
                'cost_unit': line.cost_unit,
                'phase_id': line.phase_id.id,
                'is_variation': True,
                'variation_id': self.id,
            }))
        
        cost_sheet.write({'line_ids': new_lines})
        self.write({'state': 'approved'})
        
        # Notify Project Manager
        if self.project_id.user_id:
            msg = _("Variation Order Approved: %s for Project %s. Total Adjustment: %s") % (
                self.name, self.project_id.name, self.total_amount
            )
            self.notify_contact(self.project_id.user_id.partner_id, msg, title="Scope Change Approved")

    def action_reject(self):
        self.write({'state': 'rejected'})

class ConstructionVariationLine(models.Model):
    _name = 'construction.variation.line'
    _description = 'Variation Order Line'

    variation_id = fields.Many2one('construction.variation.order', string='Variation Order')
    cost_type = fields.Selection([
        ('material', 'Material'),
        ('labor', 'Labor'),
        ('overhead', 'Overhead'),
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment')
    ], string='Type', required=True, default='material')
    
    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Char(string='Description')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    
    quantity = fields.Float(string='Variation Quantity', default=1.0)
    cost_unit = fields.Float(string='Unit Cost')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one('res.currency', related='variation_id.currency_id')

    @api.depends('quantity', 'cost_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.cost_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.display_name
            self.cost_unit = self.product_id.standard_price
