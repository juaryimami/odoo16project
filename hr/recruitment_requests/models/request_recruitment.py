from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class RecruitmentRequest(models.Model):
    _name = 'recruitment.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Recruitment Request"
    _rec_name = 'order_reference'

    order_reference = fields.Char(string='REFERENCE', required=True, copy=False, readonly=True,
                                  default=lambda self: _("New"))
    request_date = fields.Date(string='Request Date', default=fields.Date.today())
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    wanted_job_position = fields.Many2one('hr.job', string='Job Title', required=True)
    number_of_wanted_employees = fields.Integer(string='Number of staffs required', required=True)
    request_department = fields.Many2one('hr.department', string='Department/Area')
    place_of_work = fields.Char(string='Place of Work')
    accountable_to = fields.Char(string='Accountable To')
    age_limit_min = fields.Integer(string='Age Limit Min')
    age_limit_max = fields.Integer(string='Age Limit Max')
    occupational_grad = fields.Char(string='Occupational Grade')
    salary_start = fields.Float(string='Start')
    salary_end = fields.Float(string='End')

    brief_outline_of_duties = fields.Html(string='Duties')
    term_employment = fields.Many2one('hr.contract.type', string='Term of Employment')
    contract_from = fields.Date(string='Contract From')
    contract_to = fields.Date(string='Contract To')
    reason_to_vacant = fields.Char(string='Reason of vacant post')
    shortest_possible_date = fields.Integer(string='Shortest possible date needed to file the vacant post')

    requirement_line_ids = fields.One2many('recruitment.requirement.line', 'recruitment_request_id',
                                           string='Requirements')
    qualification_line_ids = fields.One2many('qualification.requirement.line', 'recruitment_request_id',
                                           string='Qualification')
    skill_line_ids = fields.One2many('skill.requirement.line', 'recruitment_request_id',
                                           string='Skill')

    requested_by = fields.Many2one('hr.employee', string='Requested By')
    approved_by = fields.Many2one('hr.employee', string='Approved By')
    verified_by = fields.Many2one('hr.employee', string='Verified By')
    authorized_by = fields.Many2one('hr.employee', string='Authorized By')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('tobe_approve', 'Department Approve'),
        ('approve', 'HR Approve'),
        ('done', 'GM Approved'),
        ('recuirtmented', 'Recruitment Done'),
        ('reject', 'Reject')], default='draft', string="Status")
    is_used = fields.Boolean(string='Is Used', default=False)
    

    @api.constrains('number_of_wanted_employees')
    def _check_number_of_mp(self):
        for record in self:
            if record.number_of_wanted_employees <=0:
                raise ValidationError(_('Number of wanted employees must be > 0'))

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_from < record.request_date:
                raise ValidationError(_('Expected  Date cannot be before the Request Date.'))

    def action_tobe_approve(self):
        self.state = 'tobe_approve'

    def action_approve(self):
        self.state = 'approve'

    def action_reject(self):
        self.state = 'reject'

    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        self.state = 'draft'

    def action_recruitment_done(self):
        self.state = 'recuirtmented'

    @api.model
    def create(self, vals):
        if vals.get('order_reference', _('New')) == _('New'):
            vals['order_reference'] = self.env['ir.sequence'].next_by_code('recruitment.request') or _('New')
        return super(RecruitmentRequest, self).create(vals)

    @api.depends('additional_employees', 'replacement_employees')
    def _compute_total_wanted_employees(self):
        for record in self:
            record.number_of_wanted_employees = record.additional_employees + record.replacement_employees

    promotion_button_visible = fields.Boolean(
        compute='_compute_promotion_button_visible',
        store=False
    )

    @api.depends('state')
    def _compute_promotion_button_visible(self):
        for record in self:
            record.promotion_button_visible = self.env['ir.config_parameter'].sudo().get_param(
                'employee_promotion.promotion_button_visible', default=True)


class EducationLevel(models.Model):
    _name = 'education_level.recruitment'
    _description = "Education Level"

    name = fields.Char(string="Education Level", required=True)
    description = fields.Text(string='Description')

class EducationType(models.Model):
    _name = 'education_type.recruitment'
    _description = "Education Type"

    name = fields.Char(string="Education Type", required=True)
    description = fields.Text(string='Description')

class ExperienceLevel(models.Model):
    _name = 'experience_level.recruitment'
    _description = "Experience Level"

    name = fields.Char(string="Experience Level", required=True)
    description = fields.Text(string='Description')

class RecruitmentRequirementLine(models.Model):
    _name = 'recruitment.requirement.line'
    _description = 'Recruitment Requirement Line'

    education_type_id = fields.Many2one('education_type.recruitment', string='Education Type')
    education_level_id = fields.Many2one('education_level.recruitment', string='Education Level')
    experience_year = fields.Many2one('experience_level.recruitment', string='Experience Year')
    recruitment_request_id = fields.Many2one('recruitment.request', string='Recruitment Request')

class QualificationRequirementLine(models.Model):
    _name = 'qualification.requirement.line'
    _description = 'Qualification Requirement Line'
    name = fields.Char(string="Qualification", required=True)
    description = fields.Char(string="Description")
    recruitment_request_id = fields.Many2one('recruitment.request', string='Recruitment Request')


class SkillRequirementLine(models.Model):
    _name = 'skill.requirement.line'
    _description = 'Skill Requirement Line'
    recruitment_request_id = fields.Many2one('recruitment.request', string='Recruitment Request')
    name = fields.Char(string="Skill", required=True)
    description = fields.Char(string="Description")

