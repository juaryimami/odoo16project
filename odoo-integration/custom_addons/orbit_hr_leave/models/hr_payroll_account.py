# pyrefly: ignore [missing-import]
from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    account_debit = fields.Many2one('account.account', string='Debit Account', company_dependent=True)
    account_credit = fields.Many2one('account.account', string='Credit Account', company_dependent=True)


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    journal_id = fields.Many2one('account.journal', string='Salary Journal', company_dependent=True)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    move_id = fields.Many2one('account.move', string='Accounting Entry', readonly=True, copy=False)

    def action_payslip_done(self):
        """
        Override to generate accounting entries when a payslip is validated.
        """
        res = super(HrPayslip, self).action_payslip_done()

        for payslip in self:
            if payslip.move_id:
                continue

            if not payslip.struct_id.journal_id:
                # If no journal is set, we skip accounting integration to not block the flow
                # (Graceful fallback if accounting isn't configured)
                continue

            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = payslip.date_to or payslip.date_from

            name = _('Payslip of %s') % (payslip.employee_id.name)

            for line in payslip.details_by_salary_rule_category:
                amount = line.total
                if not amount:
                    continue
                
                rule = line.salary_rule_id
                if rule.account_debit:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': payslip.employee_id.address_home_id.id,
                        'account_id': rule.account_debit.id,
                        'journal_id': payslip.struct_id.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if rule.account_credit:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': payslip.employee_id.address_home_id.id,
                        'account_id': rule.account_credit.id,
                        'journal_id': payslip.struct_id.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            # Check balance
            if line_ids:
                if round(debit_sum, 2) != round(credit_sum, 2):
                    msg = _("Accounting Integration Skipped: Debits (%(debit)s) do not equal Credits (%(credit)s). Please check your Salary Rule account configurations.", debit=debit_sum, credit=credit_sum)
                    payslip.message_post(body=msg, message_type="notification")
                    continue

                move_dict = {
                    'narration': name,
                    'ref': payslip.number,
                    'journal_id': payslip.struct_id.journal_id.id,
                    'date': date,
                    'line_ids': line_ids,
                }
                try:
                    move = self.env['account.move'].create(move_dict)
                    move.action_post()
                    payslip.write({'move_id': move.id})
                except Exception as e:
                    payslip.message_post(body=_("Failed to create Journal Entry: %s", str(e)), message_type="notification")

        return res
