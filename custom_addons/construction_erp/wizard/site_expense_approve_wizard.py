# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SiteExpenseApproveWizard(models.TransientModel):
    _name = 'construction.site.expense.approve.wizard'
    _description = 'Wizard to Select Budget Line during Expense Approval'

    expense_id = fields.Many2one('construction.site.expense', string='Expense Request', required=True)
    job_order_id = fields.Many2one('construction.job.order', string="Job Order")
    
    overhead_line_id = fields.Many2one(
        'construction.job.resource.line', 
        string='Allocate to Overhead Line', 
        required=True,
        domain="[('job_order_id', '=', job_order_id), ('resource_type', '=', 'overhead')]"
    )
    
    amount = fields.Monetary(string='Final Approved Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='expense_id.currency_id')
    description = fields.Char(string='Final Description', required=True)

    def action_confirm(self):
        self.ensure_one()
        if not self.overhead_line_id:
            raise UserError(_("Please select an overhead budget line to proceed."))
            
        # Call the actual approval logic with adjusted values
        return self.expense_id._process_approval_with_line(
            self.overhead_line_id, 
            final_amount=self.amount, 
            final_description=self.description
        )
