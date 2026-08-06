# pyrefly: ignore [missing-import]
from odoo import models, fields, api
# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('request_date_from', 'holiday_status_id', 'state', 'attachment_ids')
    def _check_orbit_leave_rules(self):
        for leave in self:
            if leave.state in ['cancel', 'refuse']:
                continue

            leave_type = leave.holiday_status_id
            employee = leave.employee_id
            contract = employee.contract_id

            # 1. Probation Check
            # Assuming leave_type.requires_allocation == 'yes' usually applies to Annual Leaves.
            # But we can be more explicit by checking if it's not unpaid or if company policy dictates.
            # Let's enforce for all leaves except unpaid, or we can use a specific flag. 
            # For now, block if the contract has a future probation end date.
            if contract and contract.probation_end_date:
                if leave.request_date_from and leave.request_date_from <= contract.probation_end_date:
                    # Let's allow unpaid/sick leave during probation, but block Annual. 
                    # If requires_allocation == 'yes', typically it's an earned leave like Annual.
                    if leave_type.requires_allocation == 'yes':
                        raise ValidationError("Leave usage is blocked during the probation period.")

            # 2. Document Check
            if leave_type.requires_document and not leave.supported_attachment_ids and not leave.attachment_ids:
                raise ValidationError(f"A valid document (attachment) is required for {leave_type.name}.")

            # 3. Short Sick Limit (Max 2 undocumented days/year)
            if leave_type.is_short_sick:
                start_of_year = leave.request_date_from.replace(month=1, day=1)
                end_of_year = leave.request_date_from.replace(month=12, day=31)
                
                # Search for all short sick leaves in the current year
                existing_short_sick = self.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('request_date_from', '>=', start_of_year),
                    ('request_date_from', '<=', end_of_year),
                    ('id', '!=', leave.id) # exclude current if already saved
                ])
                total_days = sum(existing_short_sick.mapped('number_of_days')) + leave.number_of_days
                if total_days > 2:
                    raise ValidationError("Maximum 2 undocumented short sick days allowed per year.")

            # 4. Unpaid Leave Limit (Max 2 requests/year)
            if leave_type.is_unpaid_limited:
                start_of_year = leave.request_date_from.replace(month=1, day=1)
                end_of_year = leave.request_date_from.replace(month=12, day=31)
                
                existing_requests_count = self.env['hr.leave'].search_count([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('request_date_from', '>=', start_of_year),
                    ('request_date_from', '<=', end_of_year),
                    ('id', '!=', leave.id)
                ])
                # current request is +1
                if (existing_requests_count + 1) > 2:
                    raise ValidationError("Maximum 2 unpaid leave requests allowed per year.")

            # 5. Max Days Per Request Check
            if leave_type.max_days_per_request > 0 and leave.number_of_days > leave_type.max_days_per_request:
                raise ValidationError(f"You cannot request more than {leave_type.max_days_per_request} days at once for {leave_type.name}.")
