# -*- coding: utf-8 -*-
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date

class Author(models.Model):
    _name = 'book_club.author'
    _description = 'Book Club Author'

    user_id = fields.Many2one('res.users', string='Related User')
    name = fields.Char(string='Name', required=True)
    biography = fields.Text(string='Biography')
    birth_date = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    book_ids = fields.One2many('book_club.book', 'author_id', string='Authored Books')
    image = fields.Image(string='Profile Picture')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'An author with this name already exists!')
    ]

    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                record.age = relativedelta(date.today(), record.birth_date).years
            else:
                record.age = 0
