import pytz
from datetime import datetime, timedelta, time
from pytz import timezone, UTC
from odoo import api, Command, fields, models, tools
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    subordinate_custom_id = fields.Many2many(
        'hr.employee',  # The target model for the Many2many relation
        'employee_subordinate_rel',  # Name of the relation table
        'employee_id',  # Column in the relation table for the current model
        'subordinate_id',  # Column in the relation table for the related model
        string="Subordinates"
    )

class HrLeave(models.Model):
    _inherit = "hr.leave"

    state = fields.Selection([
        ('draft', 'Save'),
        ('confirm', 'Submit'),
        ('review', 'Review'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved'),
        ('refuse', 'Reject')
    ], string='Status', default='draft', store=True, tracking=True, copy=False,
        readonly=False,
        help="The status is set to 'To Submit', when a time off request is created." +
             "\nThe status is 'To Approve', when time off request is confirmed by user." +
             "\nThe status is 'Refused', when time off request is refused by manager." +
             "\nThe status is 'Approved', when time off request is approved by manager.")

    is_half_day_start = fields.Boolean(string="Start with Half Day")
    is_half_day_end = fields.Boolean(string="End with Half Day")
    cu_user = fields.Char(string="User", compute="compute_current_user")
    cu_email = fields.Char(string="User", compute="compute_current_user")
    cu_phone = fields.Char(string="User", compute="compute_current_user")

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['draft','review','confirm', 'validate', 'validate1'] for holiday in self):
            raise UserError(_('Time off request must be confirmed or validated in order to refuse it.'))

        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # Delete the meeting
        self.mapped('meeting_id').write({'active': False})
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()

        # Post a second message, more verbose than the tracking message
        for holiday in self:
            if holiday.employee_id.user_id:
                holiday.message_post(
                    body=_('Your %(leave_type)s planned on %(date)s has been refused',
                           leave_type=holiday.holiday_status_id.display_name, date=holiday.date_from),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self.activity_update()
        return True

    def _action_user_cancel(self, reason):
        self.ensure_one()
        if self.state in ["validate",'refuse'] :
            raise ValidationError(_('This time off cannot be canceled.'))

        self._force_cancel(reason, 'mail.mt_note')

    def compute_current_user(self):
        user=self.env.user
        self.cu_user=user.name
        self.cu_email=user.login
        self.cu_phone=user.phone

    def action_confirm(self):
        template = self.env.ref('de_hr_workspace_timeoff.leave_request_email_template_id', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        res = super(HrLeave, self).action_confirm()
        return res

    def action_refuse(self):
        template = self.env.ref('de_hr_workspace_timeoff.leave_refuse_email_template_id', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        res = super(HrLeave, self).action_refuse()
        return res

    # def action_cancel(self):
    #     template = self.env.ref('de_hr_workspace_timeoff.leave_refuse_email_template_id', raise_if_not_found=False)
    #     if template:
    #         template.send_mail(self.id, force_send=True)
    #     res = super(HrLeave, self).action_refuse()
    #     return res




    @api.onchange('date_from', 'date_to', 'is_half_day_start', 'is_half_day_end')
    def _compute_number_of_days(self):
        for leave in self:
            if leave.date_from and leave.date_to:
                # Calculate full days between the dates
                full_days = (leave.date_to - leave.date_from).days + 1

                # Adjust for half days
                if leave.is_half_day_start:
                    full_days -= 0.5
                if leave.is_half_day_end:
                    full_days -= 0.5

                leave.number_of_days = full_days
            else:
                leave.number_of_days = 0.0

    def _compute_state(self):
        for leave in self:
            leave.state = 'draft'
    
    def review_leave_request(self):
        for rec in self:
            rec.state="review"
    
    def action_approve(self):
        if any(holiday.state != 'review' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})


        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            user_tz = timezone(holiday.tz)
            utc_tz = pytz.utc.localize(holiday.date_from).astimezone(user_tz)
            holiday.message_post(
                body=_(
                    'Your %(leave_type)s planned on %(date)s has been accepted',
                    leave_type=holiday.holiday_status_id.display_name,
                    date=utc_tz.replace(tzinfo=None)
                ),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()

        template = self.env.ref('de_hr_workspace_timeoff.leave_approval_email_template_id', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        return True



    def action_validate(self):
        current_employee = self.env.user.employee_id
        leaves = self._get_leaves_on_public_holiday()
        if leaves:
            raise ValidationError(_('The following employees are not supposed to work during that period:\n %s') % ','.join(leaves.mapped('employee_id.name')))

        if any(holiday.state not in ['review','confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})

        leaves_second_approver = self.env['hr.leave']
        leaves_first_approver = self.env['hr.leave']

        for leave in self:
            if leave.validation_type == 'both':
                leaves_second_approver += leave
            else:
                leaves_first_approver += leave

            if leave.holiday_type != 'employee' or\
                (leave.holiday_type == 'employee' and len(leave.employee_ids) > 1):
                employees = leave._get_employees_from_holiday_type()

                conflicting_leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True
                ).search([
                    ('date_from', '<=', leave.date_to),
                    ('date_to', '>', leave.date_from),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('holiday_type', '=', 'employee'),
                    ('employee_id', 'in', employees.ids)])

                if conflicting_leaves:
                    # YTI: More complex use cases could be managed in master
                    if leave.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
                        raise ValidationError(_('You can not have 2 time off that overlaps on the same day.'))

                    # keep track of conflicting leaves states before refusal
                    target_states = {l.id: l.state for l in conflicting_leaves}
                    conflicting_leaves.action_refuse()
                    split_leaves_vals = []
                    for conflicting_leave in conflicting_leaves:
                        if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
                            continue

                        # Leaves in days
                        if conflicting_leave.date_from < leave.date_from:
                            before_leave_vals = conflicting_leave.copy_data({
                                'date_from': conflicting_leave.date_from.date(),
                                'date_to': leave.date_from.date() + timedelta(days=-1),
                                'state': target_states[conflicting_leave.id],
                            })[0]
                            before_leave = self.env['hr.leave'].new(before_leave_vals)
                            before_leave._compute_date_from_to()

                            # Could happen for part-time contract, that time off is not necessary
                            # anymore.
                            # Imagine you work on monday-wednesday-friday only.
                            # You take a time off on friday.
                            # We create a company time off on friday.
                            # By looking at the last attendance before the company time off
                            # start date to compute the date_to, you would have a date_from > date_to.
                            # Just don't create the leave at that time. That's the reason why we use
                            # new instead of create. As the leave is not actually created yet, the sql
                            # constraint didn't check date_from < date_to yet.
                            if before_leave.date_from < before_leave.date_to:
                                split_leaves_vals.append(before_leave._convert_to_write(before_leave._cache))
                        if conflicting_leave.date_to > leave.date_to:
                            after_leave_vals = conflicting_leave.copy_data({
                                'date_from': leave.date_to.date() + timedelta(days=1),
                                'date_to': conflicting_leave.date_to.date(),
                                'state': target_states[conflicting_leave.id],
                            })[0]
                            after_leave = self.env['hr.leave'].new(after_leave_vals)
                            after_leave._compute_date_from_to()
                            # Could happen for part-time contract, that time off is not necessary
                            # anymore.
                            if after_leave.date_from < after_leave.date_to:
                                split_leaves_vals.append(after_leave._convert_to_write(after_leave._cache))

                    split_leaves = self.env['hr.leave'].with_context(
                        tracking_disable=True,
                        mail_activity_automation_skip=True,
                        leave_fast_create=True,
                        leave_skip_state_check=True
                    ).create(split_leaves_vals)

                    split_leaves.filtered(lambda l: l.state in 'validate')._validate_leave_request()

                values = leave._prepare_employees_holiday_values(employees)
                leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                    no_calendar_sync=True,
                    leave_skip_state_check=True,
                    # date_from and date_to are computed based on the employee tz
                    # If _compute_date_from_to is used instead, it will trigger _compute_number_of_days
                    # and create a conflict on the number of days calculation between the different leaves
                    leave_compute_date_from_to=True,
                ).create(values)

                leaves._validate_leave_request()

        leaves_second_approver.write({'second_approver_id': current_employee.id})
        leaves_first_approver.write({'first_approver_id': current_employee.id})

        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        employee_requests._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
        return True

