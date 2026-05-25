from odoo import models, fields, api

class PerformanceLine(models.Model):
    _name = 'performance.lines'
    _description = 'performance lines'

    master_id = fields.Many2one("employee.performance.master", ondelete='cascade', index=True, copy=False)

    objective_id = fields.Many2one('employee.kpi',string="Objective",)
    kpi_id = fields.Char(string="Key Dept KPI", compute="_compute_kpi")
    target_date = fields.Char(string="Target Date", compute="_compute_target")
    employee_id = fields.Many2one('hr.employee')
    success = fields.Boolean(string="Success")
    partially = fields.Boolean(string="Partially")
    not_success = fields.Boolean(string='Not Success')
    remark = fields.Char(string="Remark")

    @api.depends('objective_id')
    def _compute_kpi(self):
        for rec in self:
            emp_kpi = self.env['employee.kpi'].search([('id','=', rec.objective_id.id)])
            self.kpi_id = emp_kpi.kpi

    @api.depends('objective_id')
    def _compute_target(self):
        for rec in self:
            target = self.env['employee.kpi'].search([('id', '=', rec.objective_id.id)])
            self.target_date = target.target_date

    @api.onchange('success')
    def _compute_success(self):
        for rec in self:
            if rec.success:
                rec.partially=False
                rec.not_success=False

    @api.onchange('partially')
    def _compute_partially(self):
        for rec in self:
            if rec.partially:
                rec.success = False
                rec.not_success = False

    @api.onchange('not_success')
    def _compute_not_success(self):
        for rec in self:
            if rec.not_success:
                rec.success = False
                rec. partially = False






