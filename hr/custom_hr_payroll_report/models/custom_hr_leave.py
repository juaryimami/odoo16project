from datetime import datetime, timedelta
from pytz import timezone
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round



class CustomHrLeave(models.Model):
    _inherit = 'hr.leave'

    state = fields.Selection([
        ('draft', 'Save'),
        ('confirm', 'Submit'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved'),
        ('refuse', 'Reject')
    ], string='Status', compute='_compute_state', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Submit', when a time off request is created." +
             "\nThe status is 'To Approve', when time off request is confirmed by user." +
             "\nThe status is 'Refused', when time off request is refused by manager." +
             "\nThe status is 'Approved', when time off request is approved by manager.")

    @api.depends('holiday_status_id')
    def _compute_state(self):
        for leave in self:
            # leave.state = 'confirm' if leave.validation_type != 'no_validation' else 'draft'
            leave.state = 'draft'
class CustomHrLeaveType(models.Model):
    _inherit = 'hr.leave.type'


    def name_get(self):
        if not self.requested_name_get():
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(CustomHrLeaveType, self).name_get()
        res = []
        for record in self:
            name = record.name
            employee_id = self._get_contextual_employee_id()

            if record.requires_allocation == "yes" and not self._context.get('from_manager_leave_form'):
                remain=0
                total_all=0
                leave_balance=self.env['custom.hr.leave'].search([('employee_id','=',employee_id)], limit=1)
                if leave_balance:
                    remain=leave_balance.total_remaining
                    total_all=leave_balance.total_balance


                name = "%(name)s (%(count)s)" % {
                    'name': name,
                    'count': _('%g remaining out of %g') % (
                        float_round(remain, precision_digits=2) or 0.0,
                        float_round(total_all, precision_digits=2) or 0.0,
                    ) + (_(' hours') if record.request_unit == 'hour' else _(' days'))
                }
            res.append((record.id, name))
        return res

