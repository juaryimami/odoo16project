from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class custom_hr_employee(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    department_id = fields.Many2one('hr.department', string="Project")
    # project_id = fields.Many2one('agent.project', string="Project")

    @api.model
    def default_get(self, fields_list):
        res = super(custom_hr_employee, self).default_get(fields_list)
        if 'project_id' in res:
            project_id = res['project_id']
            res['employee_ids'] = self.env['hr.employee'].search([('contract_id.project_id', '=', project_id.id)]).ids
        return res

    # @api.onchange('project_id')
    # def _onchange_project_id(self):
    #     if self.project_id:
    #         employees=self.env['hr.employee'].search([('contract_id.project_id', '=', self.project_id.id)]).ids
    #         if len(employees)>0:
    #             self.employee_ids = employees
    #         else:
    #             self.employee_ids=False
    #     else:
    #         self.employee_ids = self.env['hr.employee'].search([]).ids



class ContractHistory(models.Model):
    _inherit = 'hr.contract.history'
    job_id=fields.Many2one('hr.job')

    @api.onchange('employee_id')
    def job_id_from_employee(self):
        for rec in self:
            if rec.employee_id.job_id:
                rec.job_id=rec.employee_id.job_id.id



    def hr_contract_view_form_new_action(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('hr_contract.action_hr_contract')
        job_id=False
        if self.employee_id.job_id:
            job_id=self.employee_id.job_id.id
        action.update({
            'context': {'default_employee_id': self.employee_id.id,
                        'default_job_id':job_id},
            'view_mode': 'form',
            'view_id': self.env.ref('hr_contract.hr_contract_view_form').id,
            'views': [(self.env.ref('hr_contract.hr_contract_view_form').id, 'form')],
        })
        return action


