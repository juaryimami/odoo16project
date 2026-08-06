# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

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
    notes = fields.Text(string='Contractor Notes/Justification')

    # Certification Fields
    line_ids = fields.One2many('construction.cpr.line', 'cpr_id', string='Detailed Progress Lines')
    contract_amount = fields.Monetary(string='Total Contract Amount', compute='_compute_contract_amount', store=True)
    
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

    cpr_type = fields.Selection([
        ('advance', 'Advance Payment / Mobilization'),
        ('progress', 'Progress Claim'),
        ('final', 'Final Payment'),
        ('retention', 'Retention Release')
    ], string='Type', default='progress', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Wait Verification'),
        ('approved', 'Approved'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    inspection_id = fields.Many2one('construction.inspection', string='Work Evaluation Inspection', readonly=True)

    invoice_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)

    @api.depends('line_ids.subtotal')
    def _compute_contract_amount(self):
        for cpr in self:
            cpr.contract_amount = sum(cpr.line_ids.mapped('subtotal'))

    @api.depends('job_order_id', 'state')
    def _compute_previous_progress(self):
        for cpr in self:
            # Sum up the verified deltas of all previous approved/paid CPRs for this job order
            prev_cprs = self.search([
                ('job_order_id', '=', cpr.job_order_id.id),
                ('id', '<', cpr.id or 999999999),
                ('state', 'in', ['approved', 'invoiced', 'paid'])
            ])
            total_previous = sum(p.certified_progress - p.previous_certified_progress for p in prev_cprs)
            cpr.previous_certified_progress = total_previous

    @api.constrains('current_progress_claim')
    def _check_claim_limit(self):
        for record in self:
            if record.cpr_type == 'progress':
                if record.current_progress_claim <= 0:
                    raise ValidationError(_("Progress claim must be greater than 0%."))
                if (record.previous_certified_progress + record.current_progress_claim) > 100.01:
                    raise ValidationError(_("Cumulative progress claim cannot exceed 100%. (Current claim: %s%%, Previous total: %s%%)") % (record.current_progress_claim, record.previous_certified_progress))

    @api.onchange('job_order_id')
    def _onchange_job_order_id(self):
        if self.job_order_id:
            self.action_populate_lines()

    def action_populate_lines(self):
        for cpr in self:
            if cpr.state != 'draft':
                continue
            
            # Clear existing lines
            cpr.line_ids.unlink()
            job = cpr.job_order_id
            if not job:
                continue
                
            new_lines = []
            
            # Helper to create lines
            def add_line(group_lines, label):
                for l in group_lines:
                    vals = {
                        'name': f"[{label}] {l.name}",
                        'category': label,
                        'quantity': l.quantity or 1.0,
                        'unit_price': l.unit_cost if hasattr(l, 'unit_cost') else (l.unit_price if hasattr(l, 'unit_price') else 0.0),
                        'product_id': l.product_id.id if hasattr(l, 'product_id') and l.product_id else False,
                    }
                    # Link back to original budget source for automated spend tracking
                    if hasattr(l, 'cost_line_id') and l.cost_line_id:
                        vals['cost_line_id'] = l.cost_line_id.id if hasattr(l.cost_line_id, 'id') else l.cost_line_id
                        
                    if hasattr(l, 'cost_line_type') and l.cost_line_type:
                        vals['cost_line_type'] = l.cost_line_type
                    elif label == 'Material':
                        vals['cost_line_type'] = 'construction.cost.material.line'
                        
                    new_lines.append((0, 0, vals))

            # 1. Labor, Fleet, Equipment (Always included)
            add_line(job.labor_budget_line_ids, 'Labor')
            add_line(job.vehicle_line_ids, 'Fleet')
            add_line(job.equipment_line_ids, 'Equipment')
            
            # 2. Materials and Overhead (STRICTLY only if Full Contract)
            if job.contract_type == 'full':
                add_line(job.material_plan_ids, 'Material')
                add_line(job.overhead_budget_line_ids, 'Overhead')
                
            cpr.line_ids = new_lines

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
        records = super(ConstructionCPR, self).create(vals_list)
        # Ensure lines are populated immediately upon creation (crucial for portal submissions)
        records.filtered(lambda r: not r.line_ids).action_populate_lines()
        return records

    def action_verify(self):
        for cpr in self:
            if cpr.cpr_type == 'advance':
                # Advance payments are auto-verified
                cpr.action_approve()
            else:
                # Assign dedicated Project Inspector, fall back to Project Manager partner
                inspector = cpr.project_id.inspector_id or cpr.project_id.user_id.partner_id
                
                # Spawn a Work Evaluation Inspection with full context
                inspection = self.env['construction.inspection'].create({
                    'name': _("Work Evaluation: %s - Claim %s%%") % (cpr.job_order_id.name, cpr.current_progress_claim),
                    'job_order_id': cpr.job_order_id.id,
                    'cpr_id': cpr.id,
                    'previous_certified_progress': cpr.previous_certified_progress,
                    'current_progress_claim': cpr.current_progress_claim,
                    'inspector_id': inspector.id if inspector else False,
                    'contractor_remarks': cpr.notes,
                    'inspection_type': 'evaluation',
                    'state': 'draft'
                })
                # Add a default justification line to the inspection
                self.env['construction.inspection.line'].create({
                    'inspection_id': inspection.id,
                    'checklist_line_id': False, # Manual evaluation
                    'notes': _("Verification of cumulative progress claimed: %s%%. (Previous: %s%%)") % (cpr.certified_progress or cpr.current_progress_claim, cpr.previous_certified_progress),
                    'status': 'pass'
                })
                cpr.inspection_id = inspection.id
                cpr.write({'state': 'verify'})
                
                # --- Notifications & Mobile Alerts ---
                if inspector:
                    # Notify Inspector in Odoo
                    msg = _("📋 New Inspection Required: %s submitted a progress claim of %s%% for %s.") % (
                        cpr.contractor_id.name, cpr.current_progress_claim, cpr.job_order_id.name
                    )
                    cpr.notify_contact(inspector, msg, title=_("Field Inspection Request"))
                    
                    # In-app for Inspector (if user)
                    inspector_user = self.env['res.users'].search([('partner_id', '=', inspector.id)], limit=1)
                    if inspector_user:
                        cpr.send_in_app_notification(inspector_user, msg, title=_("Field Inspection Required"))
                    
                    # Notify Project Manager as well
                    pm_partner = cpr.project_id.user_id.partner_id
                    if pm_partner and pm_partner != inspector:
                        cpr.notify_contact(pm_partner, msg, title=_("Payment Verification Initiated"))
                    
                    # Send Formal Email based on template
                    template = self.env.ref('construction_erp.email_template_quality_inspection_request', raise_if_not_found=False)
                    if template:
                        template.send_mail(inspection.id, force_send=True)
                        cpr.message_post(body=_("Official inspection request email sent to %s.") % inspector.name)

    def action_approve(self):
        if self.cpr_type == 'progress':
            if not self.inspection_id:
                raise UserError(_("No work evaluation inspection found. Please trigger an inspection before approving."))
            if self.inspection_id.state != 'passed':
                raise UserError(_("Payment cannot be approved because the linked inspection has not passed. Current Status: %s") % self.inspection_id.state)

        if not self.certified_progress and self.cpr_type != 'advance':
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
        
        # NOTIFICATION: CPR Approved, Pending Bill Creation
        msg = _("Contractor Payment Request %s has been approved and is ready for billing.") % self.name
        if self.project_id.user_id:
            self.send_in_app_notification(self.project_id.user_id, msg, title=_("Payment Claim Approved"))
        if self.project_id.project_owner_id:
            self.send_in_app_notification(self.project_id.project_owner_id, msg, title=_("Payment Claim Approved"))

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
                'invoice_line_ids': []
            })
            
            invoice_lines = []
            pct_delta = (cpr.certified_progress - cpr.previous_certified_progress) / 100.0
            
            # Get default account
            default_expense_account = self.env['account.account'].search([
                ('account_type', '=', 'expense'),
                ('company_id', '=', cpr.company_id.id)
            ], limit=1)

            for line in cpr.line_ids:
                account = default_expense_account
                if line.product_id:
                    account = line.product_id.property_account_expense_id or line.product_id.categ_id.property_account_expense_categ_id or account

                invoice_lines.append((0, 0, {
                    'name': f"{line.name} (Progress: {cpr.certified_progress}%)",
                    'product_id': line.product_id.id if line.product_id else False,
                    'quantity': line.quantity,
                    'price_unit': line.unit_price * pct_delta,
                    'account_id': account.id if account else False,
                    'analytic_distribution': {str(cpr.project_id.analytic_account_id.id): 100} if cpr.project_id.analytic_account_id else False,
                    'cost_line_id_ref': f"{line.cost_line_type},{line.cost_line_id}" if line.cost_line_id and line.cost_line_type else False,
                }))

            # Also handle Retention Deduction as a negative line if needed, 
            # but usually it's handled in payment. If user wants it in bill:
            if cpr.retention_amount > 0:
                invoice_lines.append((0, 0, {
                    'name': _("Retention Deduction (%s%%)") % cpr.retention_percent,
                    'quantity': 1,
                    'price_unit': -cpr.retention_amount,
                    'account_id': cpr.company_id.retention_account_id.id if hasattr(cpr.company_id, 'retention_account_id') else default_expense_account.id,
                }))

            move.write({'invoice_line_ids': invoice_lines})
            cpr.invoice_id = move.id
            cpr.state = 'invoiced'
            
            # Notify Project Owner
            owner = cpr.project_id.project_owner_id
            if owner:
                msg = _("A new Construction Bill %s has been generated for Job Order %s. Your final approval is required for posting.") % (move.name, cpr.job_order_id.name)
                cpr.send_in_app_notification(owner, msg, title=_("Bill Approval Required"))
                cpr.notify_contact(owner.partner_id, msg, title=_("Payment Approval Required"))

    def action_view_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bill',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }

    def action_view_inspection(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Evaluation Inspection'),
            'res_model': 'construction.inspection',
            'view_mode': 'form',
            'res_id': self.inspection_id.id,
            'target': 'current',
        }

class ConstructionCPRLine(models.Model):
    _name = 'construction.cpr.line'
    _description = 'CPR Detailed Line'

    cpr_id = fields.Many2one('construction.cpr', string='Payment Request', ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    category = fields.Selection([
        ('Labor', 'Labor'),
        ('Fleet', 'Fleet'),
        ('Equipment', 'Equipment'),
        ('Material', 'Material'),
        ('Overhead', 'Overhead')
    ], string='Category')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Planned Qty', default=1.0)
    unit_price = fields.Float(string='Agreed Rate')
    subtotal = fields.Monetary(string='Total Budget', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one('res.currency', related='cpr_id.currency_id')

    # Link back to Cost Sheet specialized lines
    cost_line_id = fields.Integer(string='Budget Line ID')
    cost_line_type = fields.Char(string='Budget Line Model')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
