from odoo import models, fields, api

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}


class EmployeeAppraisal(models.Model):
    _name = 'employee.appraisal'
    _description = "Employee Appraisal"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    name = fields.Char(string="Reference")
    position_id = fields.Many2one('hr.job', string="Position", related='employee_id.job_id')
    work_location_id = fields.Many2one('hr.work.location', string="Work location",
                                       related='employee_id.work_location_id')
    manager_id = fields.Many2one('hr.employee', string="Appraisal Manager",
                                 default=lambda self: self._compute_default_evaluating_manager(), required=True)
    meeting_date = fields.Date(string="Meeting Date", required=True)
    employee_comments = fields.Text(string="Employee Comments")
    manager_comments = fields.Text(string="Manager")
    over_all_score = fields.Selection([
        ('excellent', 'Excellent'),
        ('very_good', 'Very good'),
        ('good', 'Good'),
        ('unsatisfactory', 'Unsatisfactory'),
        ('poor', 'Poor')
    ], string="Over all score",
        compute="_compute_evaluation_result")

    over_all_score_no = fields.Float(string="Over all score(actual)",
        compute="_compute_evaluation_result")

    state = fields.Selection([
        ('new', 'new'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ], string='State', default='new', tracking=True)
    appraisal_line_ids = fields.One2many(
        comodel_name='appraisal.lines',
        inverse_name='evaluation_id',
        string="Evaluation List",
        states=LOCKED_FIELD_STATES,
        copy=True, auto_join=True)

    @api.depends('appraisal_line_ids')
    def _compute_evaluation_result(self):
        for rec in self:
            excellent = len(rec.appraisal_line_ids.filtered(lambda line: line.excellent))
            very_good = len(rec.appraisal_line_ids.filtered(lambda line: line.very_good))
            good = len(rec.appraisal_line_ids.filtered(lambda line: line.good))
            unsatisfactory = len(rec.appraisal_line_ids.filtered(lambda line: line.unsatisfactory))
            poor = len(rec.appraisal_line_ids.filtered(lambda line: line.poor))


            total_point = (excellent * 5) + (very_good * 4) + (good * 3) + (unsatisfactory * 2)+ (poor * 2)

            max_points = len(rec.appraisal_line_ids) * 5
            weighted_score = 0
            if max_points > 0:
                weighted_score = (total_point / max_points) * 5
            if weighted_score >= 4.55:
                rec.over_all_score = 'excellent'
            elif weighted_score >= 3.45:
                rec.over_all_score = 'very_good'
            elif weighted_score >= 2.45:
                rec.over_all_score = 'good'
            elif weighted_score >= 1.55:
                rec.over_all_score = 'unsatisfactory'
            elif weighted_score >= 1:
                rec.over_all_score = 'poor'
            else:
                rec.over_all_score = False
            rec.over_all_score_no=weighted_score


    @api.onchange('employee_id')
    def _compute_default_rate_by_list(self):
        evaluation_cri = self.env['employee.kpi'].search(['|',('employee_id','=',self.employee_id.id), ('employee_id','=',False)])
        criteria = []
        self.appraisal_line_ids=False
        for ev in evaluation_cri:
            criteria.append((0, 0, {
                'kpi_id': ev.id,
                'excellent': False,
                'very_good': False,
                'good': False,
                'unsatisfactory': False,
                'poor': False,
            }))
        self.appraisal_line_ids= criteria

    def _compute_default_evaluating_manager(self):
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if employee:
            return employee.id
        return False
