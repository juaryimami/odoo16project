# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class RealEstateUnit(models.Model):
    _name = 'real_estate.unit'
    _description = 'Property Unit Asset Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Unit Profile / Number', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.template', string='Saleable Product', help="Link to the product variant in the catalog.")
    
    unit_type = fields.Selection([
        ('house', 'House'),
        ('shop', 'Shop'),
        ('apartment', 'Apartment'),
        ('plot', 'Plot')
    ], string='Classification', default='house')
    
    price = fields.Monetary(string='Base Price Per Unit', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    # Pooled Quantity Tracking
    total_quantity = fields.Integer(string='Total Units in Pool', default=1, required=True, tracking=True)
    quantity_sold = fields.Integer(string='Sold Count', compute='_compute_unit_quantities')
    quantity_reserved = fields.Integer(string='Reserved (Quotes)', compute='_compute_unit_quantities')
    quantity_available = fields.Integer(string='Available for Sale', compute='_compute_unit_quantities')
    
    size = fields.Float(string='Unit Size (sq.m)')
    
    sale_order_ids = fields.One2many('sale.order', 'unit_id', string='Sales Transactions')

    @api.depends('total_quantity', 'project_id', 'sale_order_ids.state')
    def _compute_unit_quantities(self):
        for unit in self:
            # Sold = Confirmed Sale Orders linked to this unit in this project
            confirmed_so = unit.sale_order_ids.filtered(lambda s: s.state in ['sale', 'done'])
            unit.quantity_sold = len(confirmed_so)
            
            # Reserved = Quotations (draft/sent)
            reserved_so = unit.sale_order_ids.filtered(lambda s: s.state in ['draft', 'sent'])
            unit.quantity_reserved = len(reserved_so)
            
            unit.quantity_available = unit.total_quantity - unit.quantity_sold

    def name_get(self):
        result = []
        for unit in self:
            name = unit.name
            if unit.quantity_available <= 0:
                name += " [SOLD OUT]"
            else:
                name += f" ({unit.quantity_available} left)"
            result.append((unit.id, name))
        return result
