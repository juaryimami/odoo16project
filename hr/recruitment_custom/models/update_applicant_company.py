from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UpdateApplicantCompany(models.Model):
    _name = 'update.project'
    _description = 'update applicant company'

    applicant_ids = fields.Many2many( 'hr.applicant', string='Applicants',required=True)
    company_id = fields.Many2one( 'res.company', string='Company',required=True)

    def on_save_employee_company(self):
        for rec in self:
            for applicant in rec.applicant_ids:
                applicant.sudo().write({'company_id': rec.company_id})

            return {
                'type': 'ir.actions.act_window',
                'name': 'Application',
                'res_model': 'hr.applicant',
                'domain': [('id', 'in', rec.applicant_ids.ids)],
                'view_mode': 'tree,kanban,form',
                'target': 'current'
            }









