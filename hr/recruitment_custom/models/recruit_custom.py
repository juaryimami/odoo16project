from odoo import models, fields, api


class RecruitCustom(models.Model):
    _inherit = 'hr.applicant'

    approver_by = fields.Many2one('res.users', string="Approver")
    company_id = fields.Many2one('res.company', string="Company")

#
#
# class ApplicationSummary(models.Model):
#     _inherit = 'hr.applicant'
#     comp_location = fields.Char(string="Company Location")








