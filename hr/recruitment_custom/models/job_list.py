from odoo import models, fields, api, _


class HrJobInherit(models.Model):
   _inherit = "hr.job"

   salary = fields.Float(string="Salary")
   purpose = fields.Text(string="Job Purpose")
   currency_id = fields.Many2one('res.currency', string="Currency")
   # posted_date = fields.Date(string="Posted Date")
   # deadline_date = fields.Date(string="Deadline Date")
