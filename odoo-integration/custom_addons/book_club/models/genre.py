# -*- coding: utf-8 -*-
from odoo import models, fields

class Genre(models.Model):
    _name = 'book_club.genre'
    _description = 'Book Club Genre'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'A genre with this name already exists!')
    ]
