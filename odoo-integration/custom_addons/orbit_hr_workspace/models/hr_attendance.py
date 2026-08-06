from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    state = fields.Selection([
        ('draft', 'To Approve'),
        ('approved', 'Approved'),
        ('absent', 'Absent')
    ], string='Status', default='draft', required=True, tracking=True)

    def action_approve_attendance(self):
        for attendance in self:
            if attendance.state == 'approved':
                continue
            # Optional: Check if user is the attendance_manager_id
            if attendance.employee_id.attendance_manager_id and self.env.user != attendance.employee_id.attendance_manager_id and not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
                raise UserError(_("Only the assigned Attendance Approver or an Attendance Administrator can approve this record."))
            attendance.state = 'approved'

    def action_mark_absent(self):
        for attendance in self:
            if attendance.state == 'absent':
                continue
            if attendance.employee_id.attendance_manager_id and self.env.user != attendance.employee_id.attendance_manager_id and not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
                raise UserError(_("Only the assigned Attendance Approver or an Attendance Administrator can mark this record as absent."))
            attendance.state = 'absent'
