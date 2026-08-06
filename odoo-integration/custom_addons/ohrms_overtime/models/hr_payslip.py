# -- coding: utf-8 --
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, api, fields


class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'

    overtime_ids = fields.Many2many('hr.overtime')

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """
        function used for writing overtime record in payslip
        input tree.

        """
        res = super(PayslipOverTime, self).get_inputs(contracts, date_from, date_to)
        
        contract = self.contract_id
        domain = [
            ('employee_id', '=', self.employee_id.id),
            ('contract_id', '=', self.contract_id.id),
            ('payslip_paid', '=', False)
        ]
        if 'state' in self.env['hr.attendance']._fields:
            domain.insert(2, ('state', '=', 'approved'))
        elif 'state' in self.env['hr.overtime']._fields:
            domain.insert(2, ('state', '=', 'approved'))
            
        overtime_id = self.env['hr.overtime'].search(domain)
        
        norm_amount = sum(overtime_id.mapped('ot_normal_amount'))
        night_amount = sum(overtime_id.mapped('ot_night_amount'))
        week_amount = sum(overtime_id.mapped('ot_weekend_amount'))
        hol_amount = sum(overtime_id.mapped('ot_holiday_amount'))
        
        if overtime_id:
            self.overtime_ids = overtime_id
            if norm_amount:
                res.append({
                    'name': 'Normal Overtime',
                    'code': 'OT_NORM',
                    'amount': norm_amount,
                    'contract_id': contract.id,
                })
            if night_amount:
                res.append({
                    'name': 'Night Overtime',
                    'code': 'OT_NIGHT',
                    'amount': night_amount,
                    'contract_id': contract.id,
                })
            if week_amount:
                res.append({
                    'name': 'Weekend Overtime',
                    'code': 'OT_WEEK',
                    'amount': week_amount,
                    'contract_id': contract.id,
                })
            if hol_amount:
                res.append({
                    'name': 'Public Holiday Overtime',
                    'code': 'OT_HOL',
                    'amount': hol_amount,
                    'contract_id': contract.id,
                })
        return res

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.

        """
        for recd in self.overtime_ids:
            if recd.type == 'cash':
                recd.payslip_paid = True
        return super(PayslipOverTime, self).action_payslip_done()
