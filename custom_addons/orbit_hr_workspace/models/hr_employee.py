from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_manager_id = fields.Many2one(
        'res.users', 
        string='Attendance Approver',
        help="User responsible for approving this employee's attendances."
    )
