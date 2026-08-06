# pyrefly: ignore [missing-import]
from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    structure_id = fields.Many2one('hr.payroll.structure', string='Force Salary Structure',
                                   help='Select a structure if you want to override the default structure of the selected employees for this batch.')

    def compute_sheet(self):
        """
        Overridden to support:
        1. Graceful error handling (skip failing payslips and log them).
        2. Overriding the Salary Structure for the batch.
        """
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
            batch_run = self.env['hr.payslip.run'].browse(active_id)
        else:
            run_data = {}
            batch_run = None

        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        failed_employees = []
        success_count = 0

        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            try:
                # Odoo Mates standard function to get defaults
                slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
                
                if not slip_data or not slip_data.get('value'):
                    raise Exception("Could not fetch payslip data (missing contract?).")
                
                # Check for structure override
                struct_id = self.structure_id.id if self.structure_id else slip_data['value'].get('struct_id')
                if not struct_id:
                    raise Exception("No salary structure found or provided.")

                res = {
                    'employee_id': employee.id,
                    'name': slip_data['value'].get('name', 'Payslip'),
                    'struct_id': struct_id,
                    'contract_id': slip_data['value'].get('contract_id'),
                    'payslip_run_id': active_id,
                    'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', [])],
                    'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', [])],
                    'date_from': from_date,
                    'date_to': to_date,
                    'credit_note': run_data.get('credit_note'),
                    'company_id': employee.company_id.id,
                }
                
                # Create payslip
                new_payslip = self.env['hr.payslip'].create(res)
                # Compute sheet
                new_payslip.compute_sheet()
                payslips += new_payslip
                success_count += 1
                
            except Exception as e:
                _logger.error(f"Failed to generate payslip for {employee.name}: {str(e)}")
                failed_employees.append(f"{employee.name} (Error: {str(e)})")
                
        # Post a message to the batch chatter if there is a batch run
        if batch_run:
            msg = f"<b>Payslip Batch Generation Summary:</b><br/>"
            msg += f"<ul><li><b>Success:</b> {success_count} payslips generated.</li>"
            if failed_employees:
                msg += f"<li><b>Failed:</b> {len(failed_employees)} employees skipped.</li></ul>"
                msg += "<p><b>Failed Employees Details:</b></p><ul>"
                for err in failed_employees:
                    msg += f"<li>{err}</li>"
                msg += "</ul>"
                batch_run.message_post(body=msg, message_type="notification", subtype_xmlid="mail.mt_note")
            else:
                msg += "</ul><p>All payslips generated successfully!</p>"
                batch_run.message_post(body=msg, message_type="notification", subtype_xmlid="mail.mt_note")

        return {'type': 'ir.actions.act_window_close'}
