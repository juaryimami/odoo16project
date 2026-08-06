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
# pyrefly: ignore [missing-import]
from odoo import models, fields, api


class HrContractOvertime(models.Model):
    _inherit = 'hr.contract'

    over_hour = fields.Monetary('Hour Wage')
    over_day = fields.Monetary('Day Wage')
    
    standard_daily_working_hours = fields.Float(
        string='Standard Daily Working Hours', 
        default=8.0, 
        required=True,
        help="Used to compute the exact hourly rate: Wage / 30 / Daily Hours"
    )
    
    dynamic_hourly_rate = fields.Monetary(
        string='Computed Hourly Rate', 
        compute='_compute_dynamic_hourly_rate',
        store=True
    )
    
    @api.depends('wage', 'standard_daily_working_hours')
    def _compute_dynamic_hourly_rate(self):
        for contract in self:
            if contract.standard_daily_working_hours > 0:
                contract.dynamic_hourly_rate = contract.wage / 30.0 / contract.standard_daily_working_hours
            else:
                contract.dynamic_hourly_rate = 0.0
