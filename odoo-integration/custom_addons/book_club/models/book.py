# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Book(models.Model):
    _name = 'book_club.book'
    _description = 'Book Club Book'

    title = fields.Char(string='Title', required=True)
    author_id = fields.Many2one('book_club.author', string='Author')
    publisher_id = fields.Many2one('book_club.publisher', string='Publisher')
    isbn = fields.Char(string='ISBN')
    publication_date = fields.Date(string='Publication Date')
    price = fields.Float(string='Price')
    genre_ids = fields.Many2many('book_club.genre', string='Genres')
    quantity = fields.Integer(string='Quantity', default=0)
    availability_status = fields.Selection([
        ('available', 'Available'),
        ('out_of_stock', 'Out of Stock')
    ], string='Availability Status', compute='_compute_availability', store=True)
    image_cover = fields.Image(string='Book Cover')

    _sql_constraints = [
        ('isbn_uniq', 'unique (isbn)', 'A book with this ISBN already exists!')
    ]

    @api.depends('quantity')
    def _compute_availability(self):
        for record in self:
            if record.quantity > 0:
                record.availability_status = 'available'
            else:
                record.availability_status = 'out_of_stock'
