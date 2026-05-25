from pkg_resources import require
from reportlab.lib.pagesizes import landscape

from odoo import models, fields,api
from num2words import num2words


class PayrollReportWizard(models.TransientModel):
    _name = 'hr.payroll.report1'
    _description = 'Payment Request'

    bank_id = fields.Many2one('res.partner.bank', string="Bank",required=True)
    date = fields.Date(string="Payroll Month",default=fields.Datetime.now)
    payroll_ids = fields.Many2many("custom.hr.payroll.report")
    amount_in_word = fields.Char("Amount in word", compute="compute_amount_in_word")

    @api.depends('payroll_ids')
    def compute_amount_in_word(self):
        for rec in self:
            total=sum(pay.net  for pay in rec.payroll_ids)
            total1=round(total, 2)
            rec.amount_in_word = num2words(total1)


    def action_print_report(self):
        data = {
            'bank_id':self.bank_id.bank_id.name,
            'bank_acc':self.bank_id.acc_number,
            'date':  self.date.strftime("%B %d, %Y") if self.date else None ,
            'payroll_ids': self.payroll_ids.ids,
            'amount_in_word': self.amount_in_word,
        }
        return self.env.ref('custom_hr_payroll_report.payroll_report_action_id').report_action(self, data=data)

class HrPayrollReportPDF(models.AbstractModel):
    _name = 'report.custom_hr_payroll_report.hr_report_template_id'

    def _get_report_values(self, docids, data=None):
        domain = [('status', '!=', 'cancel'), ('id', 'in', data.get('payroll_ids'))]
        # , ('id', 'in', data.get('payroll_ids'))

        docs = self.env['custom.hr.payroll.report'].search(domain)
        colum = {
            'bank': data.get('bank_id'),
            'date': data.get('date'),
            'amount_in_word': data.get('amount_in_word'),
            'bank_acc': data.get('bank_acc'),
        }

        return {
            'doc_ids': docs.ids,
            'doc_model': 'custom.hr.payroll.report',
            'docs': docs,
            'datas': data,
            'colum': colum,
        }


