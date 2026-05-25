from odoo import models, fields, api, _
from datetime import datetime

class ProbationEvaluation(models.Model):
    _name = 'probation.evaluation'


    employee_id = fields.Many2one('hr.employee')
    company_id = fields.Many2one("res.company", related="employee_id.company_id",
                                 string="Company", storable=True)
    position_id = fields.Many2one('hr.job', related='employee_id.job_id')
    date_hired = fields.Date(string="Date of hire", compute="_compute_start_date")
    # date_hired = fields.Date('hr.contract',string="Date of hire", related="employee_id.date_start")
    probation_end = fields.Date(string="Probation End Date", compute="_compute_probation_end")
    supervisor_id = fields.Many2one('hr.employee', related="employee_id.coach_id", string="Name of superivisor")

    recomendation_type = fields.Selection([
        ('end of probation', 'End of probation'),
        ('termination','Termination'),
    ], string="Recommendation type"
    )
    general_evaluation_review = fields.Text(string="General evaluation review")
    comments = fields.Text(string="Comments")

    duration = fields.Float(string="Duration", compute="_compute_duration", store=True)

    remark = fields.Text(string="Remark")

    @api.depends('date_hired')
    def _compute_duration(self):
      for rec in self:
       if rec.date_hired:
           d2 = datetime.now().date()

           date_difference = str((d2 - rec.date_hired).days)

           rec.duration = date_difference
       else:
           rec.duration = 0.0



    @api.depends('employee_id')
    def _compute_start_date(self):
        for s in self:
          recruited = self.env['hr.contract'].search(['&',('employee_id','=',s.employee_id.id),('state','=','open')])
          s.date_hired = recruited.date_start

    @api.depends('employee_id')
    def _compute_probation_end(self):
      for l in self:
        probation = self.env['hr.contract'].search(
            ['&', ('employee_id', '=', l.employee_id.id), ('state', '=', 'open')])
        l.probation_end = probation.probation_end_date


class ProbationDate(models.Model):
    _inherit = 'hr.contract'

    probation_end_date = fields.Date(string="Probation End Date")

# class CurrencyList(models.Model):
#     _name = 'currency.list'
#
#     name = fields.Float()

    # currency_id = fields.Many2one('currency.exchange.rate.wizard')


