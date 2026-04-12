# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ConstructionCPR(models.Model):
    _name = 'construction.cpr'
    _description = 'Contractor Payment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']
    _order = 'id desc'

    name = fields.Char(string='CPR Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True)
    job_order_id = fields.Many2one('construction.job.order', string='Job Order', required=True, domain="[('project_id', '=', project_id)]")
    contractor_id = fields.Many2one('res.partner', string='Contractor', related='job_order_id.contractor_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='job_order_id.currency_id')
    
    date = fields.Date(string='Request Date', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # Certification Fields
    contract_amount = fields.Monetary(string='Total Contract Amount', related='job_order_id.total_cost', store=True)
    
    previous_certified_progress = fields.Float(string='Previous Certified Progress (%)', compute='_compute_previous_progress', store=True)
    current_progress_claim = fields.Float(string='Contractor Progress Claim (%)')
    certified_progress = fields.Float(string='Certified Progress (%)', tracking=True)
    
    retention_percent = fields.Float(string='Retention (%)', default=5.0)
    
    # Calculation Fields
    gross_certified_amount = fields.Monetary(string='Gross Certified Amount', compute='_compute_amounts', store=True)
    previous_certified_amount = fields.Monetary(string='Previous Certified Amount', compute='_compute_amounts', store=True)
    current_work_certified = fields.Monetary(string='Current Work Certified', compute='_compute_amounts', store=True)
    
    retention_amount = fields.Monetary(string='Retention Deduction', compute='_compute_amounts', store=True)
    net_payable_amount = fields.Monetary(string='Net Payable Amount', compute='_compute_amounts', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Wait Verification'),
        ('approved', 'Approved'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    invoice_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)

    @api.depends('job_order_id')
    def _compute_previous_progress(self):
        for cpr in self:
            prev_cprs = self.search([
                ('job_order_id', '=', cpr.job_order_id.id),
                ('id', '<', cpr.id or 999999999),
                ('state', 'not in', ['draft', 'cancel'])
            ], order='id desc', limit=1)
            cpr.previous_certified_progress = prev_cprs.certified_progress if prev_cprs else 0.0

    @api.depends('certified_progress', 'contract_amount', 'retention_percent', 'previous_certified_progress')
    def _compute_amounts(self):
        for cpr in self:
            cpr.gross_certified_amount = (cpr.certified_progress / 100.0) * cpr.contract_amount
            cpr.previous_certified_amount = (cpr.previous_certified_progress / 100.0) * cpr.contract_amount
            
            # Current work is the difference
            diff_amount = cpr.gross_certified_amount - cpr.previous_certified_amount
            cpr.current_work_certified = max(diff_amount, 0.0)
            
            # Retention on current work
            cpr.retention_amount = (cpr.retention_percent / 100.0) * cpr.current_work_certified
            cpr.net_payable_amount = cpr.current_work_certified - cpr.retention_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.cpr') or _('New')
        return super(ConstructionCPR, self).create(vals_list)

    def action_verify(self):
        self.write({'state': 'verify'})

    def action_approve(self):
        if not self.certified_progress:
            raise UserError(_("Please enter the Certified Progress % before approving."))
        
        # Budget Overrun Validation
        if self.certified_progress > 100.0 or self.gross_certified_amount > self.contract_amount:
            msg = _("Certification Overrun Alert for CPR %s: Gross certified amount (%s) exceeds contract value (%s).") % (
                self.name, self.gross_certified_amount, self.contract_amount
            )
            if self.project_id.user_id:
                self.notify_contact(self.project_id.user_id.partner_id, msg, title="Contract Overrun Alert")
            self.message_post(body=msg)
            
        self.write({'state': 'approved'})

    def action_create_bill(self):
        for cpr in self:
            if cpr.state != 'approved':
                raise UserError(_("Only approved CPRs can be billed."))
            
            move = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': cpr.contractor_id.id,
                'invoice_date': fields.Date.context_today(self),
                'job_order_id': cpr.job_order_id.id,
                'cpr_id': cpr.id,
                'invoice_line_ids': [(0, 0, {
                    'name': f"Work Progress Certification {cpr.certified_progress}% for {cpr.job_order_id.name}",
                    'quantity': 1,
                    'price_unit': cpr.net_payable_amount,
                    'account_id': cpr.contractor_id.property_account_payable_id.id,
                    'analytic_distribution': {str(cpr.project_id.analytic_account_id.id): 100} if cpr.project_id.analytic_account_id else False,
                })]
            })
            cpr.invoice_id = move.id
            cpr.state = 'invoiced'

    def action_view_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }
