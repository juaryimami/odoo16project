# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class QualityInspection(models.Model):
    _name = 'construction.inspection'
    _description = 'Quality Inspection Gate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Inspection Reference', required=True)
    milestone_id = fields.Many2one('construction.job.milestone', string='Target Milestone', required=True)
    job_order_id = fields.Many2one('construction.job.order', string='Related Job Order', related='milestone_id.job_order_id', store=True)
    project_id = fields.Many2one('project.project', string='Project', related='milestone_id.job_order_id.project_id', store=True)
    task_id = fields.Many2one('project.task', string='Task / Phase', related='milestone_id.job_order_id.task_id', store=True)
    inspector_id = fields.Many2one('res.users', string='Inspector', default=lambda self: self.env.user, tracking=True)
    date = fields.Date(string='Inspection Date', default=fields.Date.context_today)
    
    state = fields.Selection([
        ('draft', 'Draft / Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed / Needs Rework')
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Overall Remarks')
    line_ids = fields.One2many('construction.inspection.line', 'inspection_id', string='QA Checklist')
    ncr_ids = fields.One2many('construction.ncr', 'inspection_id', string='Linked NCRs')
    ncr_count = fields.Integer(compute='_compute_ncr_count')

    def _compute_ncr_count(self):
        for record in self:
            record.ncr_count = len(record.ncr_ids)

    def action_generate_ncr(self):
        self.ensure_one()
        return {
            'name': _('New NCR from Inspection'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.ncr',
            'view_mode': 'form',
            'context': {
                'default_project_id': self.project_id.id,
                'default_inspection_id': self.id,
                'default_non_conformance_desc': _("Failed inspection: %s. Notes: %s") % (self.name, self.notes or ''),
            }
        }

    def action_view_ncrs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Linked NCRs',
            'res_model': 'construction.ncr',
            'view_mode': 'tree,form',
            'domain': [('inspection_id', '=', self.id)],
        }

    def write(self, vals):
        res = super(QualityInspection, self).write(vals)
        if 'state' in vals:
            for record in self:
                if vals['state'] == 'passed':
                    # Approve Milestone
                    if record.milestone_id:
                        record.milestone_id.state = 'approved'
                        # Trigger automated billing if this was the last gate
                        record.milestone_id.action_generate_bill()
                    
                    # Approve Job Order
                    if record.job_order_id:
                        record.job_order_id.state = 'approved'
                        record.job_order_id.message_post(body=_("Quality Gate PASSED. Job Order approved for final closure."))

                elif vals['state'] == 'failed':
                    # Move Job Order to Rework
                    if record.job_order_id:
                        record.job_order_id.state = 'rework'
                        msg = _("Quality Gate FAILED for %s. Rework requested by inspector.") % record.name
                        record.job_order_id.notify_contact(record.job_order_id.contractor_id, msg, title=_("Inspection Failure Notification"))
        return res

class QualityInspectionLine(models.Model):
    _name = 'construction.inspection.line'
    _description = 'Inspection Checklist Item'

    inspection_id = fields.Many2one('construction.inspection', string='Inspection', ondelete='cascade')
    name = fields.Char(string='Checklist Item', required=True)
    is_checked = fields.Boolean(string='Pass')
    notes = fields.Char(string='Remarks')
