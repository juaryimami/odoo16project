# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionScrap(models.Model):
    _name = 'construction.scrap'
    _description = 'Wastage & Scrap Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, default='New')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    product_id = fields.Many2one('product.product', string='Material', required=True, domain="[('type', '=', 'product')]", tracking=True)
    quantity = fields.Float(string='Quantity Wasted', required=True, default=1.0, tracking=True)
    reason = fields.Text(string='Reason for Loss')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Reported By', default=lambda self: self.env.user)
    scrap_id = fields.Many2one('stock.scrap', string='Odoo Scrap Record', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated')
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.scrap') or 'New'
        return super(ConstructionScrap, self).create(vals_list)

    def action_validate(self):
        for record in self:
            scrap_location = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1)
            scrap = self.env['stock.scrap'].create({
                'product_id': record.product_id.id,
                'scrap_qty': record.quantity,
                'product_uom_id': record.product_id.uom_id.id,
                'origin': record.name,
                'scrap_location_id': scrap_location.id if scrap_location else False
            })
            scrap.action_validate()
            record.write({
                'state': 'validated',
                'scrap_id': scrap.id
            })
