# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pytz
from datetime import datetime, time

class AttendanceGeneratorWizard(models.TransientModel):
    _name = 'orbit.attendance.generator.wizard'
    _description = 'Generate Attendances'

    def _default_employee(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=_default_employee)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)

    def action_generate_attendances(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("Start Date cannot be after End Date."))
            
        employee = self.employee_id
        if not employee.resource_calendar_id:
            raise UserError(_("The selected employee does not have a Working Schedule assigned."))
            
        tz = pytz.timezone(employee.tz or self.env.user.tz or 'UTC')
        
        # Localize dates to timezone, then convert to UTC for the interval function
        start_dt_local = tz.localize(datetime.combine(self.date_from, time.min))
        end_dt_local = tz.localize(datetime.combine(self.date_to, time.max))
        
        start_dt_utc = start_dt_local.astimezone(pytz.utc)
        end_dt_utc = end_dt_local.astimezone(pytz.utc)
        
        # Get all working intervals for this employee (automatically excludes approved leaves)
        intervals = employee.resource_calendar_id._work_intervals_batch(
            start_dt_utc, end_dt_utc, resources=employee.resource_id
        )[employee.resource_id.id]
        
        attendance_obj = self.env['hr.attendance']
        attendances_created = 0
        
        for interval in intervals:
            # interval is a tuple (start_datetime, end_datetime, attendance_record)
            # these datetimes are tz-aware (often in the calendar's timezone), we must convert to UTC naive for Odoo ORM
            check_in_utc = interval[0].astimezone(pytz.utc).replace(tzinfo=None)
            check_out_utc = interval[1].astimezone(pytz.utc).replace(tzinfo=None)
            
            # Create the attendance record
            # We check if there's already an attendance overlapping this time to avoid duplicates
            existing = attendance_obj.search([
                ('employee_id', '=', employee.id),
                ('check_in', '<', check_out_utc),
                '|', ('check_out', '=', False), ('check_out', '>', check_in_utc)
            ])
            
            if not existing:
                attendance_obj.create({
                    'employee_id': employee.id,
                    'check_in': check_in_utc,
                    'check_out': check_out_utc,
                })
                attendances_created += 1
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Attendances Generated'),
                'message': _('Successfully created %s attendance records.', attendances_created),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
