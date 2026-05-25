from odoo import models, fields

class TaxRegion(models.Model):
    _name = 'tax.region'
    _description = 'Tax Region'
    _rec_name='tax_region_name'

    tax_region_name = fields.Char(string='Region Name', required=True)
    description = fields.Text(string='Description')


