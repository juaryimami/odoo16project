from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    pf_rate = fields.Float(string="PF rate", store=True, compute="_compute_employee_pf")

    @api.depends('employee_id')
    def _compute_employee_pf(self):
        for record in self:
            if record.employee_id:
                pf_rate = self.env['consent.request.form'].search(
                    [('state', '=', 'approved'), ('employee_id', '=', record.employee_id.id)],
                    limit=1
                )
                hr_cont = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id)], limit=1)
                if pf_rate and hr_cont:
                    record.pf_rate = hr_cont.wage * pf_rate.contribute_percent / 100
                else:
                    record.pf_rate = 0.0
            else:
                record.pf_rate = 0.0

    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        for record in self:
            if record.pf_rate:
                pf_input = {
                    'name': 'Provident Fund Employee',
                    'code': 'EMPR',
                    'contract_id': record.contract_id.id,
                    'amount': record.pf_rate,
                }
                res.append(pf_input)
        return res

    def compute_pf_for_batch(self, contract_id):
        pf = 0.0
        hr_cont = self.env['hr.contract'].search([('id', '=', contract_id)], limit=1)
        if hr_cont:
            pf_rate = self.env['consent.request.form'].search(
                [('state', '=', 'approved'), ('employee_id', '=', hr_cont.employee_id.id)],
                limit=1
            )
            if pf_rate:
                pf = hr_cont.wage * pf_rate.contribute_percent / 100
        return pf
