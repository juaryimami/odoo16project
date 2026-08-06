from odoo import api, fields, models
from datetime import datetime, time

class HrContract(models.Model):
    _inherit = 'hr.contract'

    probation_working_days = fields.Integer(
        string='Probation Working Days',
        help="Number of working days for probation. Defaults to company setting.",
        default=lambda self: self.env.company.probation_working_days
    )

    probation_end_date = fields.Date(
        string='Probation End Date',
        compute='_compute_probation_end_date',
        store=True,
        readonly=False,
        help="Date when the employee's probation period finishes. Automatically computed based on working days."
    )

    @api.depends('date_start', 'probation_working_days', 'resource_calendar_id')
    def _compute_probation_end_date(self):
        for contract in self:
            # Preserve existing dates for already-created contracts
            if contract.id and contract.probation_end_date:
                continue
                
            if contract.date_start and contract.probation_working_days:
                if contract.resource_calendar_id:
                    # Convert date_start to datetime at midnight
                    start_dt = datetime.combine(contract.date_start, time.min)
                    # Use the resource calendar to skip weekends and holidays
                    end_dt = contract.resource_calendar_id.plan_days(contract.probation_working_days, start_dt)
                    contract.probation_end_date = end_dt.date() if end_dt else contract.date_start
                else:
                    # Fallback if no working schedule is assigned (just add raw days, though rare)
                    from dateutil.relativedelta import relativedelta
                    contract.probation_end_date = contract.date_start + relativedelta(days=contract.probation_working_days)
            else:
                contract.probation_end_date = False
