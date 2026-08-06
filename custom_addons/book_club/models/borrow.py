# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Borrow(models.Model):
    _name = 'book_club.borrow'
    _description = 'Book Club Borrow'

    book_id = fields.Many2one('book_club.book', string='Book', required=True)
    member_id = fields.Many2one('book_club.member', string='Member', required=True)
    loan_date = fields.Date(string='Loan Date', default=fields.Date.context_today, required=True)
    due_date = fields.Date(string='Due Date', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('borrowed', 'Borrowed'),
        ('pending_return', 'Pending Return'),
        ('returned', 'Returned')
    ], string='Status', default='draft', required=True, tracking=True)
    
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_is_overdue', store=True)

    @api.depends('due_date', 'status')
    def _compute_is_overdue(self):
        for record in self:
            if record.due_date and record.status in ['borrowed', 'pending_return'] and record.due_date < fields.Date.today():
                record.is_overdue = True
            else:
                record.is_overdue = False

    @api.constrains('book_id', 'member_id', 'status')
    def _check_duplicate_borrow(self):
        for record in self:
            if record.status in ['borrowed', 'pending_return']:
                existing_borrow = self.env['book_club.borrow'].search([
                    ('id', '!=', record.id),
                    ('book_id', '=', record.book_id.id),
                    ('member_id', '=', record.member_id.id),
                    ('status', 'in', ['borrowed', 'pending_return'])
                ], limit=1)
                if existing_borrow:
                    raise ValidationError(_('This member has already borrowed this book and not returned it yet.'))

    def action_borrow(self):
        for record in self:
            if record.status == 'draft':
                if record.book_id.quantity <= 0:
                    raise ValidationError(_('This book is currently not available.'))
                record.book_id.quantity -= 1
                record.status = 'borrowed'

    def action_request_return(self):
        for record in self:
            if record.status == 'borrowed':
                record.status = 'pending_return'

    def action_approve_return(self):
        for record in self:
            if record.status in ['borrowed', 'pending_return']:
                record.book_id.quantity += 1
                record.status = 'returned'
