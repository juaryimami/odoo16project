# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.constrains('line_ids')
    def _check_negative_net_salary(self):
        for payslip in self:
            net_line = payslip.line_ids.filtered(lambda l: l.code == 'NET')
            if net_line and net_line.total < 0:
                raise ValidationError(_(
                    "Payslip for %s cannot have a negative Net Salary (%s). "
                    "Please check the deductions and input lines."
                ) % (payslip.employee_id.name, net_line.total))

    def get_sick_leave_payment_ratio(self, total_sick_days_taken_in_year):
        """
        Calculates the sick leave payment ratio based on the total number of sick days 
        the employee has taken in the current calendar year.
        Tier 1: 1st 30 days -> 100% paid (ratio 1.0)
        Tier 2: Next 60 days (days 31-90) -> 50% paid (ratio 0.5)
        Tier 3: After 90 days -> Unpaid (ratio 0.0)
        
        Note: This is meant to be called from a Salary Rule python code.
        Example Usage in Salary Rule:
            ratio = payslip.get_sick_leave_payment_ratio(cumulative_sick_days)
            result = contract.wage / 30 * number_of_sick_days_in_payslip * ratio
        """
        # If the day falls within the first 30 days
        if total_sick_days_taken_in_year <= 30:
            return 1.0
        # If the day falls within the next 60 days (up to 90 days total)
        elif total_sick_days_taken_in_year <= 90:
            return 0.5
        # Any days after 90 are unpaid
        else:
            return 0.0

    def calculate_sick_leave_allowance(self):
        """
        Advanced helper that evaluates the specific sick leave days IN THIS PAYSLIP
        and applies the tiered calculation, returning the total amount to pay for sick leave.
        """
        # 1. Find all sick days recorded in this payslip's work entries
        # Assuming the work entry type for sick leave has a specific code, e.g., 'LEAVE120' or custom.
        # This requires the user to pass or define the exact work entry type code for Sick Leave.
        # For a generic implementation, we'll assume sick leave is mapped to a specific work entry type.
        
        # We need the employee's total sick days taken *before* this payslip period
        start_of_year = self.date_from.replace(month=1, day=1)
        
        # Get historical approved sick leave (requires document = medical sick leave usually)
        # We could also just sum up the number of days from historical payslip work entries.
        historical_sick_leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('request_date_from', '>=', start_of_year),
            ('request_date_from', '<', self.date_from),
            ('holiday_status_id.requires_document', '=', True) # Standard medical sick leave
        ])
        
        historical_days = sum(historical_sick_leaves.mapped('number_of_days'))
        
        # Find sick days in current payslip
        # This relies on the 'worked_days_line_ids'
        # Let's say we find a line with code 'SICK'
        current_sick_lines = self.worked_days_line_ids.filtered(lambda l: l.code == 'SICK')
        current_sick_days = sum(current_sick_lines.mapped('number_of_days'))
        
        if not current_sick_days:
            return 0.0

        daily_wage = self.contract_id.wage / 30.0 # Standard 30 day divisor
        total_allowance = 0.0
        
        # Calculate day by day
        for day in range(1, int(current_sick_days) + 1):
            cumulative_day = historical_days + day
            ratio = self.get_sick_leave_payment_ratio(cumulative_day)
            total_allowance += (daily_wage * ratio)
            
        return total_allowance

    def get_remaining_annual_leave_payout(self):
        """
        Calculates the cash payout for all unused Annual Leave days 
        belonging to this employee, meant to be called on a final payslip.
        """
        # Find the annual leave type. We'll assume it's the one requiring allocation
        # or we could specifically search for a named one, but requiring allocation is safer.
        # Another approach is to get ALL remaining allocated leaves that can be encashed.
        # Let's get all remaining leaves where the type requires allocation (Annual Leave).
        
        annual_leave_types = self.env['hr.leave.type'].search([
            ('requires_allocation', '=', 'yes')
        ])
        
        total_remaining_days = 0.0
        # Odoo 16 manages balances in hr.leave.report, but the easiest way is to sum allocations minus taken
        # for the specific employee and leave types.
        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.employee_id.id),
            ('holiday_status_id', 'in', annual_leave_types.ids),
            ('state', '=', 'validate')
        ])
        
        for alloc in allocations:
            # Add up remaining
            total_remaining_days += (alloc.number_of_days - alloc.leaves_taken)
            
        # Payout based on daily wage
        daily_wage = self.contract_id.wage / 30.0
        
        return total_remaining_days * daily_wage

    def get_ytd_amount(self, code):
        """
        Returns the Year-to-Date (YTD) total amount for a given salary rule code for this payslip's employee, 
        starting from January 1st of the payslip's year up to the payslip's end date.
        """
        self.ensure_one()
        if not self.date_to:
            return 0.0
            
        start_of_year = self.date_to.replace(month=1, day=1)
        
        self.env.cr.execute("""
            SELECT sum(pl.total)
            FROM hr_payslip_line pl
            JOIN hr_payslip p ON pl.slip_id = p.id
            WHERE p.employee_id = %s
            AND p.state = 'done'
            AND p.date_to >= %s
            AND p.date_to <= %s
            AND pl.code = %s
        """, (self.employee_id.id, start_of_year, self.date_to, code))
        
        result = self.env.cr.fetchone()
        return result[0] or 0.0


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']

    def action_send_payslips_by_email(self):
        """
        Sends the payslip by email to all employees in the batch whose payslips are validated (done).
        """
        self.ensure_one()
        valid_slips = self.slip_ids.filtered(lambda s: s.state == 'done' and s.employee_id.work_email)
        
        if not valid_slips:
            raise ValidationError(_("No validated payslips found in this batch with valid employee emails."))

        mail_template = self.env.ref('hr_payroll_community.payslip_email_template', raise_if_not_found=False)
        if not mail_template:
            raise ValidationError(_("Payslip Email Template not found."))

        for slip in valid_slips:
            # Replicating slip.action_send_email() but with force_send=False to queue them async
            email_values = {
                'email_from': self.env.user.work_email,
                'email_to': slip.employee_id.work_email,
                'subject': slip.name
            }
            mail_template.sudo().send_mail(slip.id, force_send=False, email_values=email_values)
            
        self.message_post(body=_("Payslips successfully queued for emailing to %s employees.") % len(valid_slips))

