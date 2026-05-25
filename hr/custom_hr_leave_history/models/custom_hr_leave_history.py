import datetime
from odoo import _, api, fields, models
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
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


class CustomHrLeaveBalance(models.AbstractModel):
    _inherit = 'hr.employee.base'
    last_year_leave_balance = fields.Float(string="Last Year", compute='_compute_leave_balances')
    this_year_leave_balance = fields.Float(string="This Year", compute='_compute_leave_balances')


    def _compute_leave_balances(self):
        for rec in self:
            leave = self.env['custom.hr.leave'].search([('employee_id','=', rec.id)], limit=1)
            if leave:
                rec.this_year_leave_balance = leave.current_year_entitlement
                rec.last_year_leave_balance = leave.last_year
            else:
                rec.this_year_leave_balance = 0
                rec.last_year_leave_balance = 0

    def return_to_leave_list(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Leaves',
                'res_model': 'custom.hr.leave',
                'view_mode': 'tree',
                'target': 'current',
                'context': {
                    'default_employee_id': rec.id,
                },
                'domain': [('employee_id', '=', rec.id)],
            }

# class MailActivity(models.Model):
#     _inherit = 'mail.activity'

    # @api.model
    # def create(self, values):
    #     rec = super(MailActivity, self).create(values)
    #     assigned_user = self.env['res.users'].browse(values['user_id'])
    #
    #     if rec.res_model and rec.res_id:
    #         related_record = self.env[rec.res_model].browse(rec.res_id)
    #         current_user_email = self.env.user.email
    #         notification_ids=False
    #         if assigned_user:
    #             notification_ids = [(0, 0,
    #                                  {
    #                                      'res_partner_id': assigned_user.partner_id.id,
    #                                      'notification_type': 'inbox'
    #                                  }
    #                                  )]
    #
    #         mail = self.env['mail.mail'].create({
    #             'subject': 'New Task Assigned',
    #             'email_from': current_user_email,
    #             'email_to': assigned_user.email,
    #             'body_html': f"Hello Dear {assigned_user.name},<br/><br/>"
    #                          f"Please review the task.<br/><br/>Best regards!!",
    #             # Optionally add 'reply_to' if needed
    #             'reply_to': current_user_email,
    #         })
    #         if mail:
    #             mail.send()
    #         if hasattr(related_record, 'message_post'):
    #             related_record.message_post(
    #                 subject='New activity',
    #                 body=f"Hello Dear {assigned_user.name},<br/><br/>"
    #                      f"Please review the task.<br/>{rec.summary}<br/><br/>Best regards!!",
    #                 message_type='notification',
    #                 notification_ids= notification_ids,
    #                 # partner_ids=[assigned_user.partner_id.id]
    #             )
    #         else:
    #             _logger.warning("Related record does not support message_post.")
    #     else:
    #         _logger.warning("No res_model or res_id found for the activity.")
    #     return rec

    # def write(self, vals):
    #     for activity in self:
    #         is_done = vals.get('state') == 'done'
    #         assigned_user = activity.user_id
    #         employee = self.env['hr.employee'].search([('user_id', '=', activity.user_id.id)], limit=1)
    #         related_record = self.env[activity.res_model].browse(activity.res_id)
    #         if is_done and employee and employee.supervisor_name and employee.supervisor_name.user_id:
    #             supervisor_email = employee.supervisor_name.user_id.email
    #             current_user_email = self.env.user.email or "no-reply@example.com"  # Fallback email if needed

    #             if supervisor_email:
    #                 mail = self.env['mail.mail'].create({
    #                     'subject': f'Task {activity.activity_type_id.display_name or "Activity"} is done',
    #                     'email_from': current_user_email,
    #                     'email_to': supervisor_email,
    #                     'body_html': "<p>Task has been marked as Done.<br/><br/>Best regards!!</p>",
    #                     'reply_to': supervisor_email,
    #                 })
    #                 if mail:
    #                     mail.send()

    #                 if hasattr(related_record, 'message_post'):
    #                     related_record.message_post(
    #                         body=_(F" activity assigned for {assigned_user.name} has been marked as Done."),
    #                         partner_ids=[(4,employee.supervisor_name.user_id.id)],
    #                         message_type='notification'
    #                     )
    #                 else:
    #                     _logger.warning("Related record does not support message_post.")
    #             else:
    #                 _logger.warning("No res_model or res_id found for the activity.")

    #     return super(MailActivity, self).write(vals)


    # def action_done(self):
    #     for activity in self:
    #         is_done = activity.state == 'done'
    #         assigned_user = activity.user_id
    #         employee = self.env['hr.employee'].search([('user_id', '=', activity.user_id.id)], limit=1)
    #         related_record = self.env[activity.res_model].browse(activity.res_id)
    #         if employee and employee.supervisor_name and employee.supervisor_name.user_id:
    #             supervisor_email = employee.supervisor_name.user_id.email
    #             current_user_email = self.env.user.email or "no-reply@example.com"  # Fallback email if needed
    #             notification_ids=False
    #
    #             if employee.supervisor_name.user_id:
    #                 notification_ids = [(0, 0,
    #                                     {
    #                                         'res_partner_id': employee.supervisor_name.user_id.partner_id.id,
    #                                         'notification_type': 'inbox'
    #                                     }
    #                                     )]
    #
    #             if supervisor_email:
    #                 mail = self.env['mail.mail'].create({
    #                     'subject': f'Task {activity.activity_type_id.display_name or "Activity"} is done',
    #                     'email_from': current_user_email,
    #                     'email_to': supervisor_email,
    #                     'body_html': "<p>Task has been marked as Done.<br/><br/>Best regards!!</p>",
    #                     'reply_to': supervisor_email,
    #                 })
    #                 if mail:
    #                     mail.send()
    #
    #                 if hasattr(related_record, 'message_post'):
    #                     related_record.message_post(
    #                         subject='Activity Done',
    #                         body=_(F" activity {activity.summary} assigned for {assigned_user.name} has been marked as Done."),
    #                         message_type='notification',
    #                         notification_ids= notification_ids,
    #                         # partner_ids=[employee.supervisor_name.user_id.partner_id.id]
    #                     )
    #                 else:
    #                     _logger.warning("Related record does not support message_post.")
    #             else:
    #                 _logger.warning("No res_model or res_id found for the activity.")
    #
    #     res = super(MailActivity, self).action_done()
    #     return res

