# models/consent_request_form.py

from odoo import models, fields, api

class ConsentRequestForm(models.Model):
    _name = 'consent.request.form'
    _description = 'Consent Request Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    date = fields.Date(string='Date', default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    requested_to = fields.Many2one('hr.department', string='TO')
    department_id = fields.Many2one('hr.department', string='Department',compute="_onchange_employee_id",store=True, readonly=True)
    company_name = fields.Char(string='Company Name', compute="_onchange_employee_id",store=True, Required=True)
    designation = fields.Char(string='Designation')
    location = fields.Char(string='Location', compute="_onchange_employee_id", store=True, readonly=True)
    contribute_percent = fields.Float(string='Contribute Percent')
    formal_request_letter = fields.Text(string='Formal Request Letter', compute='_compute_formal_request_letter', store=True)
    static_image = fields.Char(string='Static Image URL', default='consent_request_form\static\src\img\default_image.png')
    signature = fields.Char(string="Signature")
    attachment = fields.Binary(string='Attachment')
    attachment_name = fields.Char(string='Attachment Filename')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', string="Status", track_visibility='onchange', copy=False)

    def action_submit(self):
        self.state = 'submitted'

    def action_review(self):
        self.state = 'review'

    def action_approve(self):
        self.state = 'approved'

    def action_reject(self):
        self.state = 'rejected'

    @api.depends('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.department_id = rec.employee_id.department_id.id
                rec.company_name = rec.employee_id.company_id.name
                rec.location = rec.employee_id.company_id.partner_id.city
            else:
                rec.department_id = False
                rec.company_name = False
                rec.location = False
    
    @api.depends('contribute_percent')
    def _compute_formal_request_letter(self):
        for record in self:
            # Generate the static text along with the dynamic field value
            contribute_percent_text = "{:.2f}".format(record.contribute_percent) if record.contribute_percent else "0.00"
            record.formal_request_letter = f"""
            Dear Sir/ Madam,

            I hereby give my free consent to contribute {contribute_percent_text}% as provident fund on my full Basic Salary and not on any other allowances.
            I understand that you will also contribute the employer share (4%) in my name on my said basic salary, excluding all other allowances.
            I also undertake to abide by the rules framed to administer the provident fund and any amendments made from time to time.

            Kindly accept my above declaration.

            Yours sincerely,
            """

    def print_report_consent_request_form(self):
        report_name = 'consent.request.form.report'
        report = self.env['ir.actions.report']._get_report_from_name(report_name)

        # Pass attachment data to the report rendering context
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'attachment': self.attachment,
                'attachment_name': self.attachment_name,
            },
        }

        return report.render(self.ids, data=data)

