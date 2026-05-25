from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    reference_num = fields.Many2one(
        'recruitment.request',
        string="Reference",
        tracking=True,
        domain=[('state', '=', 'done')],
        ondelete='restrict'
    )

    department_id = fields.Many2one(
        'hr.department',
        string="Department"
    )

    job_id = fields.Many2one(
        'hr.job',
        string="Job Position"
    )

    @api.onchange('reference_num')
    def _onchange_reference_num(self):
        if self.reference_num:
            self.department_id = self.reference_num.request_department.id
            self.job_id = self.reference_num.wanted_job_position.id
        else:
            self.department_id = False
            self.job_id = False

    # @api.model
    # def create(self, vals):
    #     if not vals.get('reference_num'):
    #         raise UserError(_("Please select a reference before creating the applicant."))
    #
    #     reference = self.env['recruitment.request'].browse(vals['reference_num'])
    #
    #     # Copy the department and job position from the recruitment request to the applicant
    #     vals['department_id'] = reference.request_department.id
    #     vals['job_id'] = reference.wanted_job_position.id
    #
    #     department_before_save = reference.request_department.name
    #     print("Department Before Save:", department_before_save)
    #
    #     applicant = super(HrApplicant, self).create(vals)
    #     return applicant

    def unlink(self):
        for applicant in self:
            if applicant.reference_num:
                applicant.reference_num.is_used = False  # Mark the reference as not used if applicant is deleted
        return super(HrApplicant, self).unlink()





# from odoo import models, fields, api, _
# from odoo.exceptions import UserError
#
#
# class HrApplicant(models.Model):
#     _inherit = 'hr.applicant'
#
#
#
#
#     reference_num = fields.Many2one(
#         'recruitment.request',
#         string="Reference",
#         tracking=True,
#         domain=[('state', '=', 'done')],
#         ondelete='restrict'
#     )
#
#
#     @api.onchange('reference_num')
#     def _onchange_reference_num(self):
#         if self.reference_num:
#             # print("Reference selected:", self.reference_num)
#             # print("Department:", self.reference_num.request_department)
#             self.department_id = self.reference_num.request_department.id
#             self.job_id = self.reference_num.wanted_job_position.id
#         else:
#             self.department_id = False
#             self.job_id = False
#
#     @api.model
#     def create(self, vals):
#         if not vals.get('reference_num'):
#             raise UserError(_("Please select a reference before creating the applicant."))
#
#         reference = self.env['recruitment.request'].browse(vals['reference_num'])
#
#         # Copy the department and job position from the recruitment request to the applicant
#         vals['department_id'] = reference.request_department.id
#         vals['job_id'] = reference.wanted_job_position.id
#
#         department_before_save = reference.request_department.name
#         print("Department Before Save:", department_before_save)
#
#         applicant = super(HrApplicant, self).create(vals)
#         return applicant
#
#     def unlink(self):
#         for applicant in self:
#             if applicant.reference_num:
#                 applicant.reference_num.is_used = False  # Mark the reference as not used if applicant is deleted
#         return super(HrApplicant, self).unlink()
#
