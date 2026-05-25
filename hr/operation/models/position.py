# from odoo import models, fields
#
# class EdomiasPosition(models.Model):
#     _name = 'edomias.position'
#     _description = 'Edomias Position Types'
#
#     name = fields.Char(string='Position Name', required=True)
#     description = fields.Text(string='Position Description')
#     create_date = fields.Datetime(string="Created Date", readonly=True, default=fields.Datetime.now)
#     # Add other common fields for position types
#
#     def name_get(self):
#         result = []
#         for record in self:
#             result.append((record.id, record.name))
#         return result