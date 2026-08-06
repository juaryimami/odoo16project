# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError

class RealEstateUnit(models.Model):
    _name = 'real_estate.unit'
    _description = 'Property Unit Asset Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _check_manager_access(self):
        if not self.env.user.has_group('construction_erp.group_construction_manager'):
            raise AccessError(_("Adding or updating Real Estate Assets is only permitted for Project Managers."))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_manager_access()
        for vals in vals_list:
            # AUTO-CREATE PRODUCT: If no product is selected, create one automatically
            if not vals.get('product_id') and vals.get('name'):
                product = self.env['product.template'].create({
                    'name': vals.get('name'),
                    'list_price': vals.get('price', 0.0),
                    'is_real_estate_asset': True,
                    'type': 'service', # Real estate units are often services or special types
                    'sale_ok': True,
                    'purchase_ok': False,
                })
                vals['product_id'] = product.id
        return super(RealEstateUnit, self).create(vals_list)

    def write(self, vals):
        self._check_manager_access()
        return super(RealEstateUnit, self).write(vals)

    def unlink(self):
        for unit in self:
            if unit.quantity_sold > 0:
                raise UserError(_(
                    "Security Constraint: You cannot delete the asset unit '%s' because it has %d units already sold. "
                    "Preservation of sales history is mandatory."
                ) % (unit.name, unit.quantity_sold))
        return super(RealEstateUnit, self).unlink()

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
    quantity_sold = fields.Integer(string='Sold Count', compute='_compute_unit_quantities', store=True)
    quantity_reserved = fields.Integer(string='Reserved (Quotes)', compute='_compute_unit_quantities', store=True)
    quantity_available = fields.Integer(string='Available for Sale', compute='_compute_unit_quantities', store=True)
    
    size = fields.Float(string='Unit Size (sq.m)')
    
    @api.constrains('total_quantity')
    def _check_quantity_sold(self):
        for unit in self:
            if unit.total_quantity < unit.quantity_sold:
                raise UserError(_(
                    "Validation Error: Total Units (%d) cannot be less than the number of units already sold (%d) for '%s'. "
                    "Please adjust the pool size correctly."
                ) % (unit.total_quantity, unit.quantity_sold, unit.name))
    
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
