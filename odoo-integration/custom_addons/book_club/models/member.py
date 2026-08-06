# -*- coding: utf-8 -*-
from odoo import models, fields

class Member(models.Model):
    _name = 'book_club.member'
    _description = 'Book Club Member'

    user_id = fields.Many2one('res.users', string='Related User')
    name = fields.Char(string='Name', required=True)
    number = fields.Char(string='Member Number', required=True)
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    membership_date = fields.Date(string='Membership Date', default=fields.Date.context_today)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Membership Status', default='active')
    image = fields.Image(string='Profile Picture')
    borrow_ids = fields.One2many('book_club.borrow', 'member_id', string='Borrows')

    _sql_constraints = [
        ('number_uniq', 'unique (number)', 'A member with this number already exists!'),
        ('email_uniq', 'unique (email)', 'A member with this email already exists!')
    ]
