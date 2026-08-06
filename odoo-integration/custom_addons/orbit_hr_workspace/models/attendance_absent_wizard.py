# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError
import pytz
from datetime import datetime, time

class AttendanceAbsentWizard(models.TransientModel):
    _name = 'orbit.attendance.absent.wizard'
    _description = 'Bulk Absent Attendances Wizard'

    def _default_employee_ids(self):
        # Find employees where the current user is the attendance manager
        employees = self.env['hr.employee'].search([('attendance_manager_id', '=', self.env.user.id)])
        return employees.ids

    employee_ids = fields.Many2many(
        'hr.employee', 
        string='Employees',
        required=True,
        default=_default_employee_ids,
        help="Select the employees to mark as absent."
    )
    
    date_lines = fields.One2many(
        'orbit.attendance.absent.wizard.line',
        'wizard_id',
        string='Absent Dates'
    )

    def action_mark_absent(self):
        self.ensure_one()
        if not self.date_lines:
            raise UserError(_("Please add at least one date."))
            
        attendance_obj = self.env['hr.attendance']
        attendances_processed = 0
        
        for employee in self.employee_ids:
            if not employee.resource_calendar_id:
                continue
                
            tz = pytz.timezone(employee.tz or self.env.user.tz or 'UTC')
            
            for line in self.date_lines:
                absent_date = line.date
                
                start_dt_local = tz.localize(datetime.combine(absent_date, time.min))
                end_dt_local = tz.localize(datetime.combine(absent_date, time.max))
                
                start_dt_utc = start_dt_local.astimezone(pytz.utc)
                end_dt_utc = end_dt_local.astimezone(pytz.utc)
                
                intervals = employee.resource_calendar_id._work_intervals_batch(
                    start_dt_utc, end_dt_utc, resources=employee.resource_id
                )[employee.resource_id.id]
                
                for interval in intervals:
                    check_in_utc = interval[0].astimezone(pytz.utc).replace(tzinfo=None)
                    check_out_utc = interval[1].astimezone(pytz.utc).replace(tzinfo=None)
                    
                    # Search for existing attendance that overlaps
                    existing = attendance_obj.search([
                        ('employee_id', '=', employee.id),
                        ('check_in', '<', check_out_utc),
                        '|', ('check_out', '=', False), ('check_out', '>', check_in_utc)
                    ])
                    
                    if existing:
                        existing.write({'state': 'absent'})
                        attendances_processed += len(existing)
                    else:
                        attendance_obj.create({
                            'employee_id': employee.id,
                            'check_in': check_in_utc,
                            'check_out': check_out_utc,
                            'state': 'absent'
                        })
                        attendances_processed += 1
                        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Successfully marked %s attendance records as absent.", attendances_processed),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

class AttendanceAbsentWizardLine(models.TransientModel):
    _name = 'orbit.attendance.absent.wizard.line'
    _description = 'Bulk Absent Attendances Wizard Line'

    wizard_id = fields.Many2one('orbit.attendance.absent.wizard', string='Wizard', ondelete='cascade')
    date = fields.Date(string='Date', required=True)
