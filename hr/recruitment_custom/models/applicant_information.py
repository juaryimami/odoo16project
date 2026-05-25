from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
AVAILABLE_PRIORITIES = [
    ('0', 'Poor'),
    ('1', 'Normal'),
    ('2', 'Good'),
    ('3', 'Very Good'),
    ('4', 'Excellent'),
    ('5', 'Outstanding'),
]


class ApplicantInformation(models.Model):
    _inherit = "hr.applicant"
    _rec_name="partner_name"

    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", tracking=True)
    availability_id = fields.Many2one('applicant.availability', string="Availability", tracking=True)

    other_language = fields.Char(string="Other Language", tracking=True)
    name = fields.Char(tracking=True)
    partner_name = fields.Char(tracking=True)
    phone_two = fields.Char(string="Second Phone No.",tracking=True)
    applied_date = fields.Char(string="Applied date", tracking=True)
    applied_datetime = fields.Date(string="Applied date", default= fields.Datetime.now())
    date_application = fields.Date()
    interview_date_manual = fields.Char(string="Interview date(for previous data)", tracking=True)
    expected_salary = fields.Many2one('expected.salary', string="Expected salary", tracking=True)
    resume_grade = fields.Char(string="Resume Grade(Previous data)", tracking=True)
    remark_comment = fields.Text(string="Remark Comment", tracking=True)
    reason = fields.Many2one('reason.seeking', string="Reason For Seeking")
    interview_manual_entry_result = fields.Char(string="Interview result(for previous data)", tracking=True)
    applicant_address = fields.Char(string='Applicant Address', tracking=True)
    address_id = fields.Many2one('res.country', string="Current Address")
    resume_name = fields.Char(string="Resume Name")
    resume = fields.Binary(string="Resume")
    recruitment_job_id = fields.Many2one('recruitment.jobs', string="Recruitment Job", tracking=True)
    approver_id = fields.Many2one('res.users', string="Approver")
    language = fields.Many2many('language.skill', string="Language", tracking=True)
    year_experience = fields.Many2one('total.experience', string="Year of experience", tracking=True)
    state_id_new = fields.Many2one('res.country.state', string="State", store=True)
    benefit = fields.Many2many('expected.benefit', string="Expected benefit", tracking=True)
    experience_ids = fields.One2many('applicant.experience', 'experience_id')
    education_ids = fields.One2many('applicant.education', 'education_id')
    drop_reason = fields.Many2many('reason.drop', string="Reason For Dropping")
    reject_reason = fields.Many2many('reason.reject', string="Reason For Rejecting")
    company_id = fields.Many2one('res.company', string="Company")
    add_to_job = fields.Many2many('recruitment.jobs', string="Add to jobs")
    priority = fields.Selection(AVAILABLE_PRIORITIES, "Evaluation", default='0')

    hourly_rate_amount = fields.Integer(string="Hourly Rate Amount")

    applicant_dup_count=fields.Integer(string="Duplication", compute="compute_duplication_count")
    industry_list=fields.Char(string="Industry", compute="_compute_industry", store=True)

    @api.depends('experience_ids')
    def _compute_industry(self):
        for rec in self:
            industries = [exp.industry_id.name for exp in rec.experience_ids if exp.industry_id]
            rec.industry_list = ', '.join(industries) if industries else ""

    @api.model
    def create(self, vals):
        stage = self.env['hr.recruitment.stage'].search([('name', 'ilike', "new applicant")], limit=1)
        department = self.env['recruitment.jobs'].search([('id', '=', vals.get('recruitment_job_id'))], limit=1)
        if stage:
            vals['stage_id'] = stage.id
        if department:
            vals['department_id'] = department.department_id.id
        return super(ApplicantInformation, self).create(vals)

    def compute_duplication_count(self):
        for rec in self:
            applicants=self.env['hr.applicant'].search([('partner_name', '=', rec.partner_name),('partner_phone', '=', rec.partner_phone), ('email_from', '=', rec.email_from)])
            rec.applicant_dup_count=len(applicants)

    def return_duplicated_applicants_list(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Application',
                'res_model': 'hr.applicant',
                'domain': [('partner_name', '=', rec.partner_name),('partner_phone', '=', rec.partner_phone), ('email_from', '=', rec.email_from)],
                'view_mode': 'tree,kanban,form',
                'target': 'current'
            }

    @api.onchange('stage_id')
    def check_on_stage_update(self):
        for rec in self:
            if rec.categ_ids:
                for categ in rec.categ_ids:
                    if categ.name.lower() == "inactive":
                        raise ValidationError(_("you can't change in active user stage"))



    @api.onchange('address_id')
    def _onchange_country_id_wrapper(self):
        res = {'domain': {'state_id': []}}
        if self.address_id:
            res['domain']['state_id'] = [('address_id', '=', self.address_id.id)]
            return res

    def action_send_email_project_contact(self):
        for record in self:
            send_to=self.env['partner.list'].search([('partner_list_id', '=', record.company_id.partner_id.id)], limit=1)
            cc_to=self.env['partner.list'].search([('id', '!=',send_to.id),('partner_list_id', '=', record.company_id.partner_id.id)])
            print("cccc")
            cand_list=self.search([('id', 'in', self.ids)])
            candidates = [candidate.partner_name for candidate in cand_list if cand_list]
            contacts = [line.contact_name for line in cc_to if cc_to]
            job_postion=record.recruitment_job_id.name
            if send_to and len(candidates)>0:
                return {
                    'name': _('Send Email'),
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'view_mode': 'form',
                    'res_model': 'contact.send.email',
                    'context': {
                        'default_candidate_ids': self.ids,
                        'default_contact_id': send_to.id,
                        'default_contact_ids': cc_to.ids,
                        'default_subject': f"{job_postion}",
                        'default_message_body': (
                                f"Dear Sirs/Madam,<br/><br/>"
                                f"We would like to share with you the following candidates to be considered for the position: {job_postion}<br/>"
                                + "<br/>".join([f"{i + 1}. {candidate}" for i, candidate in enumerate(candidates)])
                                + "<br/><br/>"
                                  " Kindly review them and please let us know your feedback at your earliest.<br/> We may support you in scheduling an interview session at your convenience.<br/>  We highly appreciate your timely action in reviewing and interviewing the candidates to fill the position on time"
                                  " <br/><br> With best regards, <br/><br> The Recruitment Team"
                        ),
                    }
                }

    def update_applicant_project(self):
        return {
            'name': _('Update Applicant Company'),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'update.project',
            'context': {
                'default_applicant_ids': self.ids,
            }
        }

    def update_applicants_stage(self):

        stage=self.env['hr.recruitment.stage'].search([('name', 'ilike', "sent")], limit=1)
        for rec in self:
            cand_list = self.search([('id', 'in', self.ids)])
            candidates = [candidate.name for candidate in cand_list if cand_list]
            rec.stage_id=stage.id
            for  resp_user in rec.company_id.responsible_user_id:
                employee=self.env['hr.employee'].search([('user_id', '=', resp_user.id)], limit=1)

                if len(employee)>0 and employee.supervisor_name:
                    rec.message_post(
                        body=f"Hello Dear { employee.supervisor_name.name},<br/><br/>"
                                     f"Your Candidate {', '.join(candidates)} Moved to Sent Stage.<br/><br/>Best regards!!",
                        subject="Candidate Sent to Sent Stage",
                        message_type='notification',
                        partner_ids=[employee.supervisor_name.user_id.id]  # Send message to a specific user
                    )

    def create_employee_from_applicant(self):
        """ Create an employee from applicant """
        self.ensure_one()
        # self._check_interviewer_access()

        contact_name = False
        if self.partner_id:
            address_id = self.partner_id.address_get(['contact'])['contact']
            contact_name = self.partner_id.display_name
        else:
            if not self.partner_name:
                raise UserError(_('You must define a Contact Name for this applicant.'))
            new_partner_id = self.env['res.partner'].create({
                'is_company': False,
                'type': 'private',
                'name': self.partner_name,
                'email': self.email_from,
                'phone': self.partner_phone,
                'mobile': self.partner_mobile
            })
            self.partner_id = new_partner_id
            address_id = new_partner_id.address_get(['contact'])['contact']

        resume_type=self.env['hr.resume.line.type'].search([('name','=','Resume')],limit=1)

        employee=self.env['hr.employee'].create({
            'name': self.partner_name or contact_name,
            'job_id': self.job_id.id,
            'job_title': self.job_id.name,
            'address_home_id': address_id,
            'department_id': self.department_id.id,
            'address_id': self.company_id.partner_id.id,
            'work_email': self.department_id.company_id.email or self.email_from,
            # To have a valid email address by default
            'work_phone': self.department_id.company_id.phone,
            'applicant_id': self.ids,
            'resume_line_ids': [(0, 0, {
                'name': f"{self.partner_name or contact_name} Resume",
                'date_start': fields.Date.today(),
                'line_type_id': resume_type.id,
                'attachment_id': self.resume,  # Use the attachment ID here
            })],
        })

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.employee',
            'res_id': employee.id,  # Open the created employee record
            'target': 'current',  # Open in the current window
        }







class ApplicantEducation(models.Model):
    _name = 'applicant.education'
    _description = 'Recruitment Education Background'

    education_id = fields.Many2one('hr.applicant', string='Application', ondelete='cascade')
    degree_id = fields.Many2one('hr.recruitment.degree', string='Degree')
    major_specialization = fields.Char(string='Major Specialization', required=True)
    minor_specialization = fields.Char(string="Minor Specialization")
    gpa = fields.Char(string="GPA", required=True)
    school_name = fields.Many2one('applicant.university', string='School Name', required=True)
    
    start_date = fields.Date(string='Start Date')
    location = fields.Char(string='Location')
    end_date = fields.Date(string='End Date')
    description = fields.Text(string='Description')
    # resume = fields.Binary(string="Resume")


class ApplicantExperience(models.Model):
    _name = 'applicant.experience'
    _description = 'Recruitment Experience'

    # name = fields.Char(compute="_compute_name")
    experience_id = fields.Many2one('hr.applicant', string='Application')
    industry_id = fields.Many2one('applicant.industry', required=True, string="Industry")
    exp_position_name = fields.Char(string='Job Title', required=True)
    exp_salary = fields.Char(string="Salary")
    comp_name = fields.Char(string="Employer Name")
    emp_benefit = fields.Char(string='Current Benefit')
    comp_location = fields.Char(string="Company Location")
    
    payment_frequency = fields.Char(string="Payment Frequency")
    exp_start_date = fields.Date(string="Joined date")
    exp_currency = fields.Many2one('res.currency', string="Currency")
    end_date = fields.Date(string='End Date')
   
    exp_summary = fields.Text(string="Experience Summary")
    working_here = fields.Boolean(string="Working Here")

    @api.model
    def create(self, vals):
        if 'industry_id' in vals:
            try:
                vals['industry_id'] = int(vals['industry_id'])
            except (ValueError, TypeError):
                raise ValueError("please select industry .")
        else:
            vals['industry_id']=False
        # Example: Convert the name to uppercase
        record = super(ApplicantExperience, self).create(vals)
        return record



class ApplicantUniversity(models.Model):
    _name = 'applicant.university'
    name = fields.Char(string="University/College Name")


class ApplicantIndustry(models.Model):
    _name = 'applicant.industry'
    name = fields.Char(string="Industry")


class ReasonForSeeking(models.Model):
    _name = 'reason.seeking'
    name = fields.Char(string="Reason for seeking")


class LanguageSkill(models.Model):
    _name = 'language.skill'
    name = fields.Char(string="Language Skill")


class ExpectedSalary(models.Model):
    _name = 'expected.salary'
    name = fields.Char(string="Expected Salary Package")


class ExpectedBenefit(models.Model):
    _name = 'expected.benefit'
    name = fields.Char(string="Expected Benefit Package")


class TotalExperience(models.Model):
    _name = 'total.experience'
    name = fields.Char(string="Total Year Experience")


class ReasonDrop(models.Model):
    _name = 'reason.drop'
    name = fields.Char(string="Reason for drop")


class ReasonReject(models.Model):
    _name = 'reason.reject'
    name = fields.Char(string="Reason for reject")


class ApplicantAvailability(models.Model):
    _name = "applicant.availability"

    name = fields.Char(string="Available")
