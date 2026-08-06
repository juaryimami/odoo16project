# pyrefly: ignore [missing-import]
from odoo import models, fields

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    # Added explicit string to fix UncaughtPromiseError in Odoo 16 Javascript client
    hr_attendance_overtime = fields.Boolean(string="Attendance Overtime", compute='_compute_hr_attendance_overtime_fallback')
    
    requires_document = fields.Boolean(
        string='Requires Document',
        help='If checked, employees must attach a valid document (e.g. medical certificate) to their leave request.',
        default=False
    )
    
    def _compute_hr_attendance_overtime_fallback(self):
        for record in self:
            if hasattr(super(), '_compute_hr_attendance_overtime'):
                # Try to use standard logic if available
                record.hr_attendance_overtime = record.company_id.hr_attendance_overtime if record.company_id else self.env.company.hr_attendance_overtime
            else:
                record.hr_attendance_overtime = False
    is_short_sick = fields.Boolean(
        string='Is Short Sick Leave',
        help='If checked, this leave type will be limited to a maximum of 2 days per year.',
        default=False
    )
    is_unpaid_limited = fields.Boolean(
        string='Is Limited Unpaid Leave',
        help='If checked, employees can only make a maximum of 2 requests of this type per year.',
        default=False
    )
    is_comp_leave = fields.Boolean(
        string='Is Compensation Leave',
        help='If checked, allocations of this type will automatically expire 1 month after their start date.',
        default=False
    )
    max_days_per_request = fields.Integer(
        string='Max Days Per Request',
        help='Maximum number of consecutive days allowed for a single request of this type. 0 means unlimited.',
        default=0
    )
