# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class QualityInspection(models.Model):
    _name = 'construction.inspection'
    _description = 'Quality Inspection Gate'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']

    name = fields.Char(string='Inspection Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    milestone_id = fields.Many2one('construction.job.milestone', string='Target Milestone')
    job_order_id = fields.Many2one('construction.job.order', string='Related Job Order')
    project_id = fields.Many2one('project.project', string='Project', related='job_order_id.project_id', store=True)
    phase_id = fields.Many2one('construction.phase', string='Construction Phase', compute='_compute_phase', store=True)
    task_id = fields.Many2one('project.task', string='Task / Phase', compute='_compute_phase', store=True)

    @api.depends('job_order_id', 'milestone_id')
    def _compute_phase(self):
        for record in self:
            if record.job_order_id:
                record.phase_id = record.job_order_id.phase_id
                record.task_id = record.job_order_id.task_id
            elif record.milestone_id:
                record.phase_id = record.milestone_id.job_order_id.phase_id
                record.task_id = record.milestone_id.job_order_id.task_id
            else:
                record.phase_id = False
                record.task_id = False
    inspector_id = fields.Many2one('res.partner', string='Inspector', tracking=True)
    date = fields.Date(string='Inspection Date', default=fields.Date.context_today)
    contractor_remarks = fields.Text(string='Contractor Remarks')
    
    state = fields.Selection([
        ('draft', 'Draft / Pending'),
        ('submitted', 'Submitted'),
        ('passed', 'Passed'),
        ('failed', 'Failed / Needs Rework')
    ], string='Status', default='draft', tracking=True)

    inspection_type = fields.Selection([
        ('qa', 'Quality Assurance'),
        ('safety', 'Safety Audit'),
        ('evaluation', 'Work Evaluation (Payment Request)')
    ], string='Inspection Type', default='qa', required=True)

    cpr_id = fields.Many2one('construction.cpr', string='Related Payment Request', readonly=True)
    previous_certified_progress = fields.Float(string='Previous Certified Progress (%)')
    current_progress_claim = fields.Float(string='Current Progress Claim (%)')
    total_claim_progress = fields.Float(string='Cumulative Completion Goal (%)', compute='_compute_total_claim_progress', store=True)

    @api.depends('previous_certified_progress', 'current_progress_claim')
    def _compute_total_claim_progress(self):
        for record in self:
            record.total_claim_progress = record.previous_certified_progress + record.current_progress_claim

    access_token = fields.Char(string='Access Token', copy=False)
    is_requested = fields.Boolean(string='Is Requested', default=False)
    is_submitted = fields.Boolean(string='Is Submitted', default=False)
    portal_url = fields.Char(string='Portal URL', compute='_compute_portal_url')

    def _compute_portal_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.portal_url = f"{base_url}/inspection/public/{record.access_token}" if record.access_token else False

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

    def action_submit(self, line_vals=None):
        """ Processes the grades and updates Job Order progress. """
        self.ensure_one()
        if self.is_submitted:
            return False
            
        if line_vals:
            for line_id_str, vals in line_vals.items():
                line = self.line_ids.filtered(lambda l: str(l.id) == line_id_str)
                if line:
                    line.write(vals)
        
        # Determine overall result
        all_passed = all(line.status == 'pass' for line in self.line_ids)
        new_state = 'passed' if all_passed else 'failed'
        
        # Update Related Job Order Checklist
        for line in self.line_ids:
            if line.checklist_line_id:
                if line.status == 'pass':
                    line.checklist_line_id.write({
                        'is_done': True,
                        'verified_by': self.env.user.id if self.env.user else False
                    })
                else:
                    line.checklist_line_id.write({'is_done': False})

        self.write({
            'state': new_state,
            'is_submitted': True
        })
        
        # --- Notifications & Communication ---
        pm_partner = self.project_id.user_id.partner_id
        contractor_partner = self.job_order_id.contractor_id
        
        if new_state == 'passed':
            msg = _("🚀 Quality Inspection PASSED for %s. Work certified successfully.") % self.name
            if pm_partner:
                self.notify_contact(pm_partner, msg, title=_("Inspection Passed"))
            if contractor_partner:
                self.notify_contact(contractor_partner, msg, title=_("Work Certified"))
        else:
            msg = _("⚠️ Quality Inspection FAILED for %s. Rework has been requested.") % self.name
            if pm_partner:
                self.notify_contact(pm_partner, msg, title=_("Inspection Failure"))
            if contractor_partner:
                self.notify_contact(contractor_partner, msg, title=_("Action Required: Rework"))

        # Send formal result email to contractor
        if contractor_partner:
            template = self.env.ref('construction_erp.email_template_quality_inspection_result', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
                self.message_post(body=_("Official inspection result email sent to contractor: %s") % contractor_partner.name)

        # Handle CPR Workflow Integration for Work Evaluations
        if self.inspection_type == 'evaluation' and self.cpr_id:
            if new_state == 'passed':
                # Transfer cumulative claimed progress to certified progress but keep in verification for final approval
                self.cpr_id.write({'certified_progress': self.total_claim_progress})
                self.message_post(body=_("Linked Payment Request %s has been updated with certified progress based on inspection.") % self.cpr_id.name)
            else:
                # If inspection fails, auto-cancel the CPR
                self.cpr_id.write({'state': 'cancel'})
                self.cpr_id.message_post(body=_("Payment Request %s has been automatically cancelled because the work evaluation inspection failed.") % self.cpr_id.name)

        # Trigger Job Order State Update & Notifications
        if self.job_order_id:
            if all_passed:
                self.job_order_id.message_post(body=_("Quality Gate PASSED for: %s.") % (self.name))
                if self.milestone_id:
                    self.milestone_id.write({'state': 'approved'})
                    # Find next milestone
                    next_ms = self.job_order_id.milestone_ids.filtered(
                        lambda m: m.sequence > self.milestone_id.sequence and m.state == 'pending'
                    ).sorted('sequence')[:1]
                    if next_ms:
                        next_ms.write({'state': 'in_progress'})
                        self.job_order_id.message_post(body=_("Next execution phase activated: %s") % next_ms.name)
                    else:
                        # ALL milestones finished
                        self.job_order_id.write({'state': 'completed'})
                else:
                    # General JO inspection
                    self.job_order_id.write({'state': 'approved'})
            else:
                self.job_order_id.message_post(body=_("Quality Gate FAILED: %s. Rework required.") % self.name)
                if self.milestone_id:
                    self.milestone_id.write({'state': 'in_progress'}) # Return to In Progress for rework
                msg = _("Quality Gate FAILED for %s. Rework requested by inspector.") % self.name
                self.job_order_id.notify_contact(self.job_order_id.contractor_id, msg, title=_("Inspection Failure"))
        
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('construction.inspection') or _('New')
        
        # Auto-generate access token for portal
        import uuid
        if not vals.get('access_token'):
            vals['access_token'] = str(uuid.uuid4())
            
        record = super(QualityInspection, self).create(vals)
        return record

    def write(self, vals):
        res = super(QualityInspection, self).write(vals)
        # Note: action_submit handles status transitions now
        return res

class QualityInspectionLine(models.Model):
    _name = 'construction.inspection.line'
    _description = 'Inspection Checklist Item'

    inspection_id = fields.Many2one('construction.inspection', string='Inspection', ondelete='cascade')
    checklist_line_id = fields.Many2one('construction.job.checklist.line', string='Source Checklist Item')
    name = fields.Char(string='Instruction', related='checklist_line_id.name', readonly=True)
    status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], string='Result', default='pass')
    notes = fields.Text(string='Inspector Remarks')
