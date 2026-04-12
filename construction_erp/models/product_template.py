# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_construction_material = fields.Boolean(
        string='Is Construction Material', 
        default=False, 
        help='Check this box to categorize this product as a physical material for use within Construction Projects.'
    )
    
    is_real_estate_asset = fields.Boolean(string='Is Real Estate Asset', default=False)
    
    project_available_qty = fields.Integer(string='Project Available Assets', compute='_compute_project_pool_stats')
    project_sold_qty = fields.Integer(string='Project Sold Assets', compute='_compute_project_pool_stats')

    def _compute_project_pool_stats(self):
        for template in self:
            units = self.env['real_estate.unit'].search([('product_id', '=', template.id)])
            template.project_available_qty = sum(units.mapped('quantity_available'))
            template.project_sold_qty = sum(units.mapped('quantity_sold'))

    def action_view_project_pools(self):
        self.ensure_one()
        return {
            'name': 'Project Inventory Pools',
            'type': 'ir.actions.act_window',
            'res_model': 'real_estate.unit',
            'view_mode': 'tree,form',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id}
        }
