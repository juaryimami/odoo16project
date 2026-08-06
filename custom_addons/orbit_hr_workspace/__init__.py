# -*- coding: utf-8 -*-
from . import models


from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Retroactively approve all existing attendances so we don't break existing overtime/payroll
    attendances = env['hr.attendance'].search([('state', '=', 'draft')])
    attendances.write({'state': 'approved'})
