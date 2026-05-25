from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    piece_rate_payment = fields.Float(string="Piece Rate Payment", store=True, compute="_compute_employee_piece_rate_payment")

    @api.depends('employee_id')
    def _compute_employee_piece_rate_payment(self):
        for record in self:
            if record.employee_id:
                piece_rate_list = self.env['employee.activities'].search(
                    ['&', ('date', '>=', record.date_from), ('date', '<=', record.date_to),
                     ('employee_id', '=', record.employee_id.id)])
                record.piece_rate_payment = sum(piece_rate.employee_payment for piece_rate in piece_rate_list)
            else:
                record.piece_rate_payment = 0.0

    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        for record in self:
            commission_input = {
                'name': 'Piece Rate Payment',
                'code': 'PIECE00001',
                'contract_id': record.contract_id.id,
                'amount': record.piece_rate_payment,
            }
            res.append(commission_input)
        return res

    # def action_payslip_done(self):
    #     result = super(HrPayslip, self).action_payslip_done()
    #     for record in self:
    #         commissions = self.env['amibara.sales.commission.payment.list'].search(
    #             [('status', '=', "approved"), ('employee_id', '=', record.employee_id.id)]
    #         )
    #         for commission in commissions:
    #             commission.sudo().write({
    #                 'status': "paid"
    #             })
    #     return result

    def compute_piece_rate_for_batch(self, contract_id, date_from, date_to):
        piece_rate = 0.0
        hr_cont = self.env['hr.contract'].search( [('id', '=', contract_id)])
        if hr_cont:
            piece_rate_list = self.env['employee.activities'].search(
                ['&', ('date', '>=', date_from), ('date', '<=', date_to),
                 ('employee_id', '=', hr_cont.employee_id.id)])

            piece_rate = sum(piece_rate.employee_payment for piece_rate in piece_rate_list)
        return piece_rate


