from odoo import models, fields, api, _
from datetime import datetime

class EarlyRetirement(models.Model):
   _name = "early.retirement"
   _inherit = ['mail.thread', 'mail.activity.mixin']
   _rec_name = 'employee_id'

   employee_id = fields.Many2one('hr.employee',string="Employee")

   company_id=fields.Many2one('res.company',string="Hiring Compnay", related="employee_id.company_id")

   date_hired = fields.Date(compute="_compute_start_date", string="Date Hired")

   job_id = fields.Many2one('hr.job', related='employee_id.job_id')
   dept_id = fields.Many2one('hr.department', related="employee_id.department_id")
   date_of_birth = fields.Date( related='employee_id.birthday')
   state = fields.Selection(
      [('draft', 'Draft'),
       ('submit', 'Submitted'),
       ('review', 'Reviewed'),
       ('reject', 'Rejected'),
       ('approve', 'Approved')],
         default='draft')

   age = fields.Float(string="Age", compute="_employee_age")

   requested_date = fields.Date(string="Requested date")

   approved_by = fields.Many2one('hr.employee', string="Approved by")
   approved_date = fields.Date(string="Approved date")

   reason = fields.Text(string="Reason")
   rejection_reason = fields.Text(string="Rejection Reason")

   attachement = fields.Binary(string="Attachement")

   def action_submit(self):
      self.state = 'submit'

   def action_approve(self):
      self.state = 'approve'
      template = self.env.ref('early_retirement.early_retirement_approval_email_template_id', raise_if_not_found=False)
      if template:
         template.send_mail(self.id, force_send=True)

   def action_review(self):
      self.state = 'review'

   def action_reject(self):
      self.state = 'reject'
      template = self.env.ref('early_retirement.early_retirement_rejected_email_template_id', raise_if_not_found=False)
      if template:
         template.send_mail(self.id, force_send=True)

   @api.depends('employee_id')
   def _compute_start_date(self):
      recruited = self.env['hr.contract'].search(
         ['&', ('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
      self.date_hired = recruited.date_start


   @api.model
   @api.depends('date_of_birth')
   def _employee_age(self):
      for rec in self:
         if rec.date_of_birth:
            d2 = datetime.now().date()
            date_difference = d2.year - rec.date_of_birth.year
            rec.age =   date_difference
         else:
            rec.age = 0.0

   @api.model
   def create(self, vals):
      result = super(EarlyRetirement, self).create(vals)
      template = self.env.ref('early_retirement.early_retirement_request_email_template_id', raise_if_not_found=False)
      if template:
         template.send_mail(result.id, force_send=True)
      return result

