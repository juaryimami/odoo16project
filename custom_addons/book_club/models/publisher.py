# -*- coding: utf-8 -*-
from odoo import models, fields

class Publisher(models.Model):
    _name = 'book_club.publisher'
    _description = 'Book Club Publisher'

    user_id = fields.Many2one('res.users', string='Related User')
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    city = fields.Char(string='City')
    established_date = fields.Date(string='Established Date')
    book_ids = fields.One2many('book_club.book', 'publisher_id', string='Published Books')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'A publisher with this name already exists!')
    ]
