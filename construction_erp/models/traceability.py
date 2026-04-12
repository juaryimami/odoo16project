# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            if picking.job_order_id:
                # Sync validated moves to Job Order Consumed Materials
                consumed_lines = []
                for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
                    consumed_lines.append((0, 0, {
                        'product_id': move.product_id.id,
                        'quantity': move.quantity_done,
                        'is_consumed': True,
                    }))
                picking.job_order_id.write({'material_consumed_ids': consumed_lines})
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
