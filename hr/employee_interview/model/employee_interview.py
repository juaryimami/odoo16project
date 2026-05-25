from odoo import models, fields, api, _

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'


    interview_average = fields.Float(string="Interview Average Score", compute='_compute_average_score', storeable=True)
    interview_total = fields.Float(string="Interview Total Grade",compute="_compute_total_score_int")
    # interview_date = fields.Date(string="Interview Date", compute="_interview_date")
    white_interview_count = fields.Integer(string='Interview Count', compute='_white_compute_interview_count')

    blue_interview_count = fields.Integer(string='Interview Count', compute='_blue_compute_interview_count')

    @api.depends('name','white_interview_count')
    def _compute_average_score(self):
        for rec in self:
          if rec.white_interview_count > 0:
            sum = 0.0
            for av in self.env['employee.interview'].search(['&',('subject_id','=',rec.id),('state','=','approve')]):
                if av:
                  sum += av.average_score
            rec.interview_average = sum / rec.white_interview_count
          else:
              rec.interview_average = 0.0

    @api.depends('name', 'white_interview_count')
    def _compute_total_score_int(self):
        for rec in self:

            if rec.white_interview_count > 0:
                sum = 0.0
                for tot in self.env['employee.interview'].search(['&',('subject_id','=',rec.id),('state','=','approve')]):
                    if tot:
                     sum += tot.total_score
                    # print('printing...sum', tot.total_score)
                rec.interview_total = sum / rec.white_interview_count

            else:
                rec.interview_total = 0.0



    def _white_compute_interview_count(self):
        for rec in self:
            rec.white_interview_count = self.env['employee.interview'].search_count([('subject_id','=',rec.id)])

    # @api.depends('name', 'blue_interview_count')
    # def _compute_average_score(self):
    #     for rec in self:
    #         if rec.blue_interview_count > 0:
    #             sum = 0.0
    #             for av in self.env['employee.interview'].search(
    #                     ['&', ('subject_id', '=', rec.name)]):
    #                 if av:
    #                     sum += av.average_score
    #             rec.interview_average = sum / rec.blue_interview_count
    #         else:
    #             rec.interview_average = 0.0

    # @api.depends('name', 'blue_interview_count')
    # def _compute_total_score_int(self):
    #     for rec in self:
    #
    #         if rec.blue_interview_count > 0:
    #             sum = 0.0
    #             for tot in self.env['employee.interview'].search(
    #                     ['&', ('subject_id', '=', rec.name)]):
    #                 if tot:
    #                     sum += tot.total_score
    #                 # print('printing...sum', tot.total_score)
    #             rec.interview_total = sum / rec.blue_interview_count
    #
    #         else:
    #             rec.interview_total = 0.0

    def _blue_compute_interview_count(self):
        for rec in self:
            rec.blue_interview_count = self.env['blue.interview'].search_count(
                [('subject_id', '=', rec.id)])

    def white_interview_form_action(self):
        if self.white_interview_count>0:
            return {
                'type': 'ir.actions.act_window',
                'name': 'White Interview Form',
                'res_model': 'employee.interview',
                'domain': [('subject_id', '=', self.id)],
                'view_mode': 'tree,form',
                'target': 'current'
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'White Interview Form',
                'res_model': 'employee.interview',
                'view_mode': 'form,tree',
                'target': 'current',
                'context': {
                'default_subject_id': self.id,  # Pass the current record's ID as the default for subject_id
            }
            }


    def blue_interview_form_action(self):
        if self.blue_interview_count>0:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Blue Interview Form',
                'res_model': 'blue.interview',
                'domain': [('subject_id', '=', self.id)],
                'view_mode': 'tree,form',
                'target': 'current'
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Blue Interview Form',
                'res_model': 'blue.interview',
                'view_mode': 'form,tree',
                'target': 'current',
                'context': {
                'default_subject_id': self.id,  # Pass the current record's ID as the default for subject_id
            }
            }


class BlueInterview(models.Model):
    _name = 'blue.interview'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, default=lambda self: _('New'), readonly=True)
    subject_id = fields.Many2one('hr.applicant', string="Candidate", required=True)
    # job_id = fields.Many2one('recruitment.jobs',related='subject_id.recruitment_job_id', string="Job Position", required=True)

    candidate_name = fields.Char(string="Candidate Name")
    position = fields.Char(string="Job Position", compute="compute_job_position")
    completed_by = fields.Char(string="Completed By")
    interview_date = fields.Date(string="Interview Date")
    rate = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string="Rate")
    interviewed_by = fields.Many2many('hr.employee', string="Interviews")
    comment = fields.Text(string="Comment")
    current_salary_information = fields.Char(string="Current Salary Information")
    expected_salary = fields.Char(string="Expected Salary")
    location = fields.Char(string="Location")
    available = fields.Char(string="Available/Notice")
    strength = fields.Text(string="Candidate Strength")
    weakness = fields.Text(string="Candidate Weakness")
    blue_line_ids = fields.One2many('blue.scholar.line', 'blue_interview_id')

    @api.depends('subject_id')
    def compute_job_position(self):
        for rec in self:
            if rec.subject_id:
                rec.position = rec.subject_id.name
            else:
                rec.position = False

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('blue.interview') or _('New')
            res = super(BlueInterview, self).create(vals)
            return res

class BlueScholarInterview(models.Model):
    _name = "blue.scholar.line"

    blue_interview_id = fields.Many2one('blue.interview', ondelete='cascade')
    question_id = fields.Many2one('blue.question', string="Questions")
    ns = fields.Boolean(string="NS")
    satisfatory = fields.Boolean(string="S")
    vs = fields.Boolean(string="VS")
    na = fields.Boolean(string="NA")
    remark = fields.Char(string="Comment")


class EmployeeInterviewForm(models.Model):
    _name = 'employee.interview'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(string='Name', required=True, copy=False, default=lambda self: _('New'), readonly=True)
    # applicant_id = fields.Many2one('hr.applicant',)
    # applicant_name = fields.Char(string="Applicant Name")
    subject_id = fields.Many2one('hr.applicant', string="Candidate", required=True)
    interview_date = fields.Date(string="Interview Date")
    age = fields.Integer(string="Age")
    language_skill = fields.Char(string="Language Skill")
    department_id = fields.Many2one('hr.department',string="Department", compute="compute_department")
    salary_history = fields.Float(string="Salary History")
    reason = fields.Char(string="Reason for leaving")
    work_experience  = fields.Char(string="Work Experience")
    purpose_of_interview = fields.Selection([
        ('first_interview','First Interview'),
        ('second_interview','Second Interview'),
        ('for_client','For Client')])
    interviewed_by = fields.Many2many('hr.employee', string="Interviewed by")
    interview_type = fields.Selection([
                                       ('white_scholar','White Scholar'),
                                       ('blue_scholar','Blue Scholar')], string="Interview Type", default="white_scholar")


    availability = fields.Char(string="Availability")
    bonus = fields.Float(string="Interviewees Presentation Bonus")

    # effective_date = fields.Date(string="Interview Date", required=False)
    line_ids = fields.One2many('employee.interview.line','interview_id')
    line_count = fields.Float(compute="_compute_count")
    state = fields.Selection([('draft','Draft'),('submit','Submitted'),('approve','Approve'),('reject','Reject')],default="draft")

    total_score = fields.Float(string="Total Score", compute="_compute_score",store=True)
    completed_by = fields.Many2one('res.users',string="Assessment Completed By")
    average_score = fields.Float(string="Average Score", compute="_compute_average", store=True)

    @api.depends('subject_id')
    def compute_department(self):
        for rec in self:
            if rec.subject_id:
                rec.department_id=rec.subject_id.department_id.id
            else:
                rec.department_id=False

    # @api.depends('interview_type','line_ids.question_id')
    # def _compute_filtered_questions(self):
    #     for form in self:
    #          form.filtered_question_ids = form.line_ids.filtered(
    #                 lambda q: q.question_id.type == form.interview_type
    #             )
    # filtered_question_ids = fields.One2many(
    #     'employee.interview.line', compute='_compute_filtered_questions', string='Filtered Questions'
    # )

    @api.depends('line_ids')
    def _compute_count(self):
       for rec in self:
           rec.line_count = len(rec.line_ids)

    @api.depends('total_score','line_count')
    def _compute_average(self):

        for rec in self:
          if rec.line_count:
           rec.average_score = rec.total_score / rec.line_count
          else:
              rec.average_score = 0.0

    @api.depends('line_ids')
    def _compute_score(self):

        for rec in self:
            total = 0
            for l in rec.line_ids:
                if l.grade_id:
                    total += float(l.grade_id.name)
                    # print('printing....', l.grade_id.name)
                # total += l.grade_id.name
        self.total_score = total

    def action_approve(self):
        self.state = 'approve'

    def action_reject(self):
        self.state = 'reject'

    def action_submit(self):
        self.state = 'submit'

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.interview') or _('New')
            res = super(EmployeeInterviewForm, self).create(vals)
            return res

class EmployeeInterview(models.Model):
    _name = "employee.interview.line"

    interview_id = fields.Many2one('employee.interview',ondelete='cascade')
    question_id = fields.Many2one('interview.questions', string="Questions")
    grade_id = fields.Many2one('interview.grade', string="Grade")
    remark = fields.Char(string="Comment")


class InterviewQuestions(models.Model):
    _name = 'interview.questions'
    name = fields.Char(string="Questions", required=True)
    remark = fields.Text(string="Comment")

class BlueQuestion(models.Model):
    _name = 'blue.question'
    name = fields.Char(string="Questions", required=True)
    remark = fields.Text(string="Comment")

class InterviewGrade(models.Model):
    _name = 'interview.grade'
    name = fields.Char(string="Grade")
    remark = fields.Text(string="Remark")



