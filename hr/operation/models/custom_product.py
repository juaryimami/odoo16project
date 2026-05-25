from odoo import models, fields


class EdomiasProduct(models.Model):
    _inherit = 'product.template'
    product_number = fields.Char(string="Product Number")


