from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

class AttendanceApproveWizard(models.TransientModel):
    _name = 'orbit.attendance.approve.wizard'
    _description = 'Bulk Approve Attendances Wizard'

    def _default_date_from(self):
        return date.today().replace(day=1)

    def _default_date_to(self):
        return (date.today() + relativedelta(months=1, day=1)) - relativedelta(days=1)

    def _default_employee_ids(self):
        # Find employees where the current user is the attendance manager
        employees = self.env['hr.employee'].search([('attendance_manager_id', '=', self.env.user.id)])
        # Fallback: if not an assigned manager but has HR manager rights, default to all employees?
        # Actually, let's just return what they are assigned to, or empty if none.
        return employees.ids

    date_from = fields.Date(string='Start Date', required=True, default=_default_date_from)
    date_to = fields.Date(string='End Date', required=True, default=_default_date_to)
    employee_ids = fields.Many2many(
        'hr.employee', 
        string='Employees',
        required=True,
        default=_default_employee_ids,
        help="Select the employees whose attendances you wish to approve."
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError(_("Start Date must be before or equal to End Date."))

    def action_approve_attendances(self):
        self.ensure_one()
        
        domain = [
            ('employee_id', 'in', self.employee_ids.ids),
            ('check_in', '>=', self.date_from),
            ('check_in', '<=', self.date_to),
            ('state', '=', 'draft')
        ]
        
        attendances = self.env['hr.attendance'].search(domain)
        
        if not attendances:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("No Attendances Found"),
                    'message': _("There are no unapproved attendances for the selected employees in this date range."),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        attendances.action_approve_attendance()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Successfully approved %s attendance records." % len(attendances)),
                'sticky': False,
                'type': 'success',
            }
        }
