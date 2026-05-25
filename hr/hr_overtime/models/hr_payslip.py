from odoo import models, api, fields

class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'
    overtime_ids = fields.Many2many('overtime.calculator')

    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(PayslipOverTime, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        ot_obj = self.env['overtime.calculator'].search([('employee_id', '=', emp_id.id),('state','=','in_payment')])
        sum = 0.0
        for ot in ot_obj:
            self.overtime_ids = ot_obj
            for o in ot:
              sum += o.value
              for result in res:
                  if result.get('code') == 'OT100':
                     result['amount'] = sum
        return res

    def action_payslip_done(self):

        for st in self.env['overtime.calculator'].search([('employee_id', '=', self.employee_id.id),('state','=','in_payment')]):
            st.action_paid()
        # for rec in self.overtime_ids:
        #       rec.payslip_paid = True
        return super(PayslipOverTime, self).action_payslip_done()

