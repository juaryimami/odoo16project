from odoo import models, api, fields

class PayslipEmployeeBonus(models.Model):
    _inherit = 'hr.payslip'
    bonus_ids = fields.Many2many('employee.bonus')

    def get_inputs(self, contract_ids, date_from, date_to):

        res = super(PayslipEmployeeBonus, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        ot_obj = self.env['employee.bonus'].search(['&',('approved_date','>=',self.date_from),('approved_date','<=',self.date_to),('employee_id', '=', emp_id.id),('state','=','in_payment')])
        sum = 0.0
        for bon in ot_obj:
            self.bonus_ids = ot_obj
            for b in bon:
                if b.approved_date >= date_from and b.approved_date <= date_to:
                  sum += b.value
                  for result in res:
                   if result.get('code') == 'BON':
                     result['amount'] = sum

        return res

    def action_payslip_done(self):

        for st in self.env['employee.bonus'].search(['&',('approved_date','>=',self.date_from),('approved_date','<=',self.date_to),('employee_id', '=', self.employee_id.id),('state','=','in_payment')]):
            st.action_paid()

        return super(PayslipEmployeeBonus, self).action_payslip_done()

