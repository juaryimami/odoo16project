# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError

class ConstructionSiteExpense(models.Model):
    _name = 'construction.site.expense'
    _description = 'Site Operational Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']

    name = fields.Char(string='Reference', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    description = fields.Char(string='Description', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    
    project_id = fields.Many2one('project.project', string='Project', required=True)
    job_order_id = fields.Many2one('construction.job.order', string='Job Order', required=True, domain="[('project_id', '=', project_id)]")
    overhead_line_id = fields.Many2one('construction.job.resource.line', string='Budget Line (Overhead)', 
                                       required=False, domain="[('job_order_id', '=', job_order_id), ('resource_type', '=', 'overhead')]")
    
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Pending PM Approval'),
        ('pm_approved', 'Pending Owner Approval'),
        ('approved', 'Approved & Billed'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    invoice_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Receipts/Photos')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.site.expense') or _('New')
        return super(ConstructionSiteExpense, self).create(vals_list)

    def action_submit(self):
        self.ensure_one()
        self.state = 'submitted'
        self.message_post(body=_("Expense submitted for Project Manager approval."))
        
        # In-App Notification for Project Manager
        if self.project_id.user_id:
            msg = _("Site supervisor has submitted an expense of %s %s for your review.") % (self.amount, self.currency_id.name)
            title = _("Site Expense Approval Required: %s") % self.name
            self.send_in_app_notification(self.project_id.user_id, msg, title=title)

    def action_approve(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Please select a vendor before approval."))
            
        return {
            'name': _('Select Budget Allocation'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.site.expense.approve.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_expense_id': self.id,
                'default_job_order_id': self.job_order_id.id,
                'default_amount': self.amount,
                'default_description': self.description,
            }
        }

    def _process_approval_with_line(self, overhead_line, final_amount=None, final_description=None):
        self.ensure_one()
        # 1. Update record with potentially adjusted values and transition to pm_approved
        vals = {
            'overhead_line_id': overhead_line.id,
            'state': 'pm_approved',
        }
        if final_amount is not None:
            vals['amount'] = final_amount
        if final_description is not None:
            vals['description'] = final_description
        self.write(vals)
        
        self.message_post(body=_("Expense approved by PM. Budget allocated to %s. Awaiting final Owner sign-off.") % overhead_line.name)
        
        # Notify Owner for final approval
        if self.project_id.project_owner_id:
            msg = _("Site expense '%s' has been approved by the PM and requires your final sign-off.") % self.name
            title = _("Owner Approval Required: %s") % self.name
            self.send_in_app_notification(self.project_id.project_owner_id, msg, title=title)
            self.notify_contact(self.project_id.project_owner_id.partner_id, msg, title=title)
        return True

    def action_owner_approve(self):
        self.ensure_one()
        if self.state != 'pm_approved':
            raise UserError(_("Only expenses in 'Pending Owner Approval' can be approved by the Project Owner."))
        
        if not self.partner_id:
            raise UserError(_("Please select a vendor before approval."))
            
        # 1. Determine Financial Mapping (Product & Account)
        product_id = False
        account_id = False
        if self.overhead_line_id.cost_line_type and self.overhead_line_id.cost_line_id:
            try:
                master_line = self.env[self.overhead_line_id.cost_line_type].sudo().browse(self.overhead_line_id.cost_line_id)
                if master_line.exists() and hasattr(master_line, 'product_id') and master_line.product_id:
                    product_id = master_line.product_id.id
                    account_id = master_line.product_id.property_account_expense_id.id or \
                                 master_line.product_id.categ_id.property_account_expense_categ_id.id
            except:
                pass

        if not account_id:
            # Fallback to general site expense account
            expense_account = self.env['account.account'].sudo().search([
                ('account_type', '=', 'expense'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            account_id = expense_account.id if expense_account else False

        # 2. Create High-Fidelity Vendor Bill with project, job_order and phase
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_id.id,
            'project_id': self.project_id.id,
            'job_order_id': self.job_order_id.id,
            'phase_id': self.job_order_id.phase_id.id if self.job_order_id.phase_id else False,
            'invoice_date': self.date,
            'is_owner_approved': True, # Owner approved it directly on the expense
            'invoice_line_ids': [(0, 0, {
                'name': f"[{self.name}] {self.description}",
                'product_id': product_id,
                'quantity': 1,
                'price_unit': self.amount,
                'account_id': account_id,
                'tax_ids': [(5, 0, 0)], # Ensure tax is NOT added on top of the requested amount
                'analytic_distribution': {str(self.project_id.analytic_account_id.id): 100.0} if self.project_id.analytic_account_id else False,
                'cost_line_id_ref': f"construction.job.resource.line,{self.overhead_line_id.id}",
            })]
        })
        move.action_post()
        
        self.write({
            'state': 'approved',
            'invoice_id': move.id
        })
        self.message_post(body=_("Expense approved by Project Owner. Vendor Bill %s generated.") % move.name)
        
        # Notify Initiator (Site Manager)
        if self.create_uid:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.create_uid.id,
                summary=_('Site Expense Approved: %s') % self.name,
                note=_('Your site expense request of %s %s has been approved by the Project Owner and billed.') % (self.amount, self.currency_id.name)
            )
        return True

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'
        self.message_post(body=_("Expense rejected."))
        
        # Notify Initiator (Site Manager)
        if self.create_uid:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.create_uid.id,
                summary=_('Site Expense Rejected: %s') % self.name,
                note=_('Your site expense request of %s %s has been rejected.') % (self.amount, self.currency_id.name)
            )

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.state == 'approved':
            raise UserError(_("Cannot reset an already billed expense."))
        self.state = 'draft'

    def action_view_bill(self):
        self.ensure_one()
        if not self.invoice_id:
            return False
        return {
            'name': _('Vendor Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }
