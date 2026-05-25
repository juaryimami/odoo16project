
from odoo import models, _, fields, api
from datetime import datetime
class RecruitmentJobs(models.Model):
    _name = 'recruitment.jobs'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Title")
    color = fields.Integer(string="Color")
    department_id = fields.Many2one('hr.department', string="Department")
    category = fields.Many2one('job.category', string="Category")
    salary = fields.Char(string="Salary")
    location = fields.Char(string="Job Location")
    deadline_date = fields.Date(string="Deadline", required=True)
    created_at = fields.Date(string="Created at")
    posted_date = fields.Date(string="Posted date")
    company_name = fields.Many2one('res.company', string="Hiring Company")
    description = fields.Html(string="Job Description")
    skill = fields.Html(string="Skills")
    employment_type = fields.Many2one('hr.contract.type')
    purpose = fields.Html(string="Job Purpose")
    currency_id = fields.Many2one('res.currency', string="Currency")
    qualification = fields.Html(string="Qualification")
    required_no = fields.Integer(string="Required Number")
    application_list_count = fields.Integer(string='Application Count', compute='_compute_application_count')
    criterion_id = fields.Many2many('job.status', string="Criterion")
    reason = fields.Char(string="Reason For Criterion")
    closed_date = fields.Date(string="Recruitment closed date")
    created_by = fields.Char(string='Created by', compute="_compute_user", storable=True)
    followed_by = fields.Char(string='Followed by', compute="_compute_follower", storable=True)
    assigned_user_id = fields.Many2one('res.users', string='Assigned Person')

    open_job_count = fields.Integer(compute='count_open_jobs')

    def count_open_jobs(self):
        for rec in self:
            rec.open_job_count= self.env['recruitment.jobs'].sudo().search_count([('state', '=', 'post')])


    def new_application_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Application',
                'res_model': 'hr.applicant',
                'view_mode': 'form,kanban,tree',
                'target': 'current',
                'context': {
                'default_recruitment_job_id': rec.id  # Set default value for the form
            }
            }


    @api.model
    def _compute_user(self):
        self.created_by = self.create_uid.name

    @api.model
    def _compute_follower(self):
        self.followed_by = self.create_uid.name

    def _compute_application_count(self):
        for rec in self:
           jobs = self.env['hr.applicant'].search_count(['|',('add_to_job','in',rec.ids),('recruitment_job_id','=',rec.id)])
           if jobs > 0:
               rec.application_list_count = jobs
           else:
               rec.application_list_count = 0



    level = fields.Selection([
        ('junior','Junior Level'),
        ('middle','Middle Level'),
        ('senior','Senior Level'),
        ('managerial','Managerial Level'),
        ], string="Career Level")
    state = fields.Selection([
        ('draft','Draft'),
        ('post','Posted'),
        ('expire','Expired'),
        ('reset', 'Reset'),
        ], default="draft")
    state_compute = fields.Selection([
        ('draft', 'Draft'),
        ('post', 'Posted'),
        ('expire', 'Expired'),
        ('reset', 'Reset'),
    ], compute="compute_job_status", default="draft")

    level_label = fields.Char(
        compute="_compute_level_label",
        string="Career Level Label"
    )

    def _compute_level_label(self):
        for record in self:
            record.level_label = dict(self._fields['level'].selection).get(record.level, "")
    @api.depends('deadline_date')
    def compute_job_status(self):
        for rec in self:
            if rec.deadline_date < fields.Date.today():
                rec.state_compute="expire"
                rec.state="expire"
            else:
                rec.state_compute = "draft"
    def action_post(self):
        self.state = "post"
        self.write({'posted_date': datetime.now().date()})

    def action_back(self):
        self.state = "draft"
        self.write({'posted_date': ''})
    def application_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Application',
                'res_model': 'hr.applicant',
                'domain': ['|',('add_to_job','in',rec.ids),('recruitment_job_id','=',rec.id)],
                'view_mode': 'kanban,tree,form',
                'target': 'current'
            }
class JobStatus(models.Model):
    _name = "job.status"
    name = fields.Char(string="Name")
    color = fields.Integer(string="Color")
class JobCategory(models.Model):
    _name = 'job.category'

    name = fields.Char(string="Category", required="Category")