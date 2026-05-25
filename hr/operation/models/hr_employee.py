from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        record = super(HrEmployee, self).create(vals)

        # Notify the user about the creation of the new employee
        if record:
            # Post a notification message in the chatter
            record.message_post(
                body=_('Congratulations! A new employee has been created successfully.'),
                subject=_('Employee Created'),
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        return record
