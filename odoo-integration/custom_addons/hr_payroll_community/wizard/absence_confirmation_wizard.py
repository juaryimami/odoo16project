from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AbsenceConfirmationWizard(models.TransientModel):
    _name = 'absence.confirmation.wizard'
    _description = 'Confirm Absence Deductions'

    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')
    message = fields.Html(string='Message', readonly=True)

    def action_compute_and_deduct(self):
        # We process the computation but set context to apply the deduction
        if not self.payslip_ids:
            return {'type': 'ir.actions.act_window_close'}
            
        return self.payslip_ids.with_context(apply_absence_deduction=True, skip_absence_wizard=True).compute_sheet()

    def action_compute_and_forgive(self):
        # We process the computation but explicitly do not apply deduction
        if not self.payslip_ids:
            return {'type': 'ir.actions.act_window_close'}
            
        return self.payslip_ids.with_context(apply_absence_deduction=False, skip_absence_wizard=True).compute_sheet()
