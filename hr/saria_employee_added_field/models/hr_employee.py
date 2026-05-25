from odoo import models, fields, api

class Employee(models.Model):
    _inherit = 'hr.employee'


    # house_number = fields.Char(string="House Number")
    supervisor_name = fields.Many2one('hr.employee',string="Immediate Supervisor")
    # Driving License Fields
    driving_license_id = fields.Char(string='Driving License ID')
    driving_license_issued_by = fields.Char(string='Issued by')
    driving_license_date_of_issuance = fields.Date(string='Date of Issuance ')
    driving_license_date_of_expire = fields.Date(string='Date of Expire ')
    driving_license_attachment = fields.Binary(string='Driving License Attachment')
    driving_license_attachment_name = fields.Char(string='Driving License Attachment Name')

    # Passport Fields
    passport_no = fields.Char(string='Passport No.')
    passport_issued_by = fields.Char(string='Issued by ')
    passport_date_of_issuance = fields.Date(string='Date of Issuance')
    passport_date_of_expire = fields.Date(string='Date of Expire ')
    passport_attachment = fields.Binary(string='Passport Attachment')
    passport_attachment_name = fields.Char(string='Passport Attachment Name')

    # Work Permit Fields
    work_permit_status = fields.Selection([('yes','Yes'),('no','No')],string="Required/Applicable")
    work_permit_no = fields.Char(string='Work Permit No.')
    work_permit_issued_by = fields.Char(string='Issued by')
    work_permit_date_of_issuance = fields.Date(string='Date of Issuance')
    work_permit_date_of_expire = fields.Date(string='Date of Expire')
    work_permit_attachment = fields.Binary(string='Work Permit Attachment')
    work_permit_attachment_name = fields.Char(string='Work Permit Attachment Name')
    # work_permit_required = fields.Selection([
    #     ('required', 'Required/applicable'),
    #     ('not_required', 'Not Required/applicable')
    # ], string='Work Permit Required')

    # @api.onchange('work_permit_status')
    # def _compute_status(self):
    #     if self.work_permit_status == 'yes':
    #         return self.work_permit_no

    # Professional License Fields
    professional_license = fields.Selection([
        ('engineering', 'Engineering'),
        ('health', 'Health'),
    ], string='Professional License type', default='engineering')
    professional_license_issued_by = fields.Char(string='Issued by')
    professional_license_date_of_issuance = fields.Date(string='Date of Issuance')
    professional_license_date_of_expire = fields.Date(string='Date of Expire ')
    professional_license_attachment = fields.Binary(string='Professional License Attachment')
    professional_license_attachment_name = fields.Char(string='Professional License Attachment Name')
    professional_license_status = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Required/Applicable")
    resume_attachment = fields.Binary(string='Documents Attachment')



