# -*- coding: utf-8 -*-
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class InstallmentPlan(models.Model):
    _name = 'real_estate.installment.plan'
    _description = 'Real Estate Installment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Reference', required=True)
    client_id = fields.Many2one('res.partner', string='Client', required=True, domain="[('is_client', '=', True)]")
    sale_id = fields.Many2one('sale.order', string='Sale Order', domain="[('partner_id', '=', client_id)]", required=True)
    unit_id = fields.Many2one('real_estate.unit', string='Property Unit Type', required=True)
    total_amount = fields.Monetary(string='Total Sale Value', related='sale_id.amount_total', store=True, currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='sale_id.currency_id')
    
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id', required=True)
    number_of_months = fields.Integer(string='Number of Months', required=True, default=12, tracking=True)
    start_date = fields.Date(string='First Installment Date', required=True, default=fields.Date.context_today)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed')
    ], string='Status', default='draft', tracking=True)
    
    @api.model
    def cron_auto_generate_invoices(self):
        """ Scans installment lines approaching their due date and issues invoices. """
        params = self.env['ir.config_parameter'].sudo()
        days_ahead = int(params.get_param('construction_erp.auto_invoice_days', default=7))
        target_date = fields.Date.context_today(self) + relativedelta(days=days_ahead)
        
        lines = self.env['real_estate.installment.line'].search([
            ('is_invoiced', '=', False),
            ('due_date', '<=', target_date),
            ('plan_id.state', '=', 'active'),
            ('plan_id.unit_id.project_id.project_type', '=', 'construction')
        ])
        for line in lines:
            line.action_create_invoice()

    line_ids = fields.One2many('real_estate.installment.line', 'plan_id', string='Installments')

    def action_generate_schedule(self):
        for plan in self:
            plan.line_ids.unlink() # Clear existing
            
            # Step 1: Create Deposit
            self.env['real_estate.installment.line'].create({
                'plan_id': plan.id,
                'name': 'Initial Deposit',
                'amount': plan.deposit_amount,
                'due_date': plan.start_date,
            })
            
            # Step 2: Calculate remaining
            remaining = plan.total_amount - plan.deposit_amount
            monthly_slice = remaining / plan.number_of_months if plan.number_of_months > 0 else 0
            
            for i in range(1, plan.number_of_months + 1):
                due_date = plan.start_date + relativedelta(months=i)
                self.env['real_estate.installment.line'].create({
                    'plan_id': plan.id,
                    'name': f'Installment {i} of {plan.number_of_months}',
                    'amount': monthly_slice,
                    'due_date': due_date,
                })
            plan.state = 'active'


class InstallmentLine(models.Model):
    _name = 'real_estate.installment.line'
    _description = 'Installment Schedule Line'

    plan_id = fields.Many2one('real_estate.installment.plan', string='Plan')
    name = fields.Char(string='Description', required=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='plan_id.currency_id')
    due_date = fields.Date(string='Due Date', required=True)
    
    invoice_id = fields.Many2one('account.move', string='Generated Invoice')
    is_invoiced = fields.Boolean(string='Invoiced', compute='_compute_is_invoiced', store=True)

    @api.depends('invoice_id', 'invoice_id.state')
    def _compute_is_invoiced(self):
        for line in self:
            line.is_invoiced = bool(line.invoice_id)

    def action_create_invoice(self):
        for line in self:
            if not line.invoice_id:
                move = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': line.plan_id.client_id.id,
                    'installment_line_id': line.id,
                    'invoice_date': fields.Date.context_today(self),
                    'invoice_date_due': line.due_date,
                    'invoice_line_ids': [(0, 0, {
                        'name': line.name + " (" + line.plan_id.unit_id.name + ")",
                        'price_unit': line.amount,
                        'quantity': 1,
                        'analytic_distribution': {str(line.plan_id.unit_id.project_id.analytic_account_id.id): 100} if line.plan_id.unit_id.project_id.analytic_account_id else False,
                    })]
                })
                line.invoice_id = move.id
