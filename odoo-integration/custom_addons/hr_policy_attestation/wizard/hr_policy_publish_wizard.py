# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrPolicyPublishWizard(models.TransientModel):
    _name = 'hr.policy.publish.wizard'
    _description = 'Publish Policy Wizard'

    template_id = fields.Many2one('hr.policy.template', string='Policy Template', required=True)
    version_num = fields.Char(string='Version Number', required=True)
    is_major = fields.Boolean(string='Major Update', default=True, help='If checked, this will force all targeted employees to sign the new version. If unchecked, employees who signed the previous version will be marked as agreed.')

    def action_publish(self):
        self.ensure_one()
        
        # 1. Create the new version record
        version_vals = {
            'template_id': self.template_id.id,
            'version_num': self.version_num,
            'is_major': self.is_major,
            'content_type': self.template_id.content_type,
            'body_html': self.template_id.body_html,
            'attachment': self.template_id.attachment,
            'attachment_name': self.template_id.attachment_name,
        }
        new_version = self.env['hr.policy.version'].create(version_vals)
        
        # 2. Update the template's current version
        self.template_id.current_version_id = new_version.id
        
        # 3. Determine target employees
        employees = self.env['hr.employee']
        if self.template_id.target_type == 'all':
            employees = self.env['hr.employee'].search([('active', '=', True)])
        elif self.template_id.target_type == 'department':
            if not self.template_id.department_ids:
                raise UserError(_("Please select at least one department for the target."))
            employees = self.env['hr.employee'].search([('department_id', 'in', self.template_id.department_ids.ids), ('active', '=', True)])
        elif self.template_id.target_type == 'specific':
            if not self.template_id.employee_ids:
                raise UserError(_("Please select at least one employee for the target."))
            employees = self.template_id.employee_ids

        if not employees:
            raise UserError(_("No active employees found for the specified target."))

        # 4. Handle attestations based on major/minor update
        attestations_to_create = []
        for emp in employees:
            status = 'pending'
            
            # If minor update, check if they already signed the previous active version
            if not self.is_major:
                old_attestation = self.env['hr.policy.attestation'].search([
                    ('employee_id', '=', emp.id),
                    ('template_id', '=', self.template_id.id),
                    ('status', '=', 'agreed')
                ], order='signed_datetime desc', limit=1)
                
                if old_attestation:
                    status = 'agreed'
            
            # Mark previous pending ones as superseded
            old_pendings = self.env['hr.policy.attestation'].search([
                ('employee_id', '=', emp.id),
                ('template_id', '=', self.template_id.id),
                ('status', '=', 'pending')
            ])
            if old_pendings:
                old_pendings.with_context(allow_status_update=True).write({'status': 'superseded'})
                
            attestations_to_create.append({
                'employee_id': emp.id,
                'version_id': new_version.id,
                'status': status,
                'signed_datetime': fields.Datetime.now() if status == 'agreed' else False,
            })
            
        if attestations_to_create:
            self.env['hr.policy.attestation'].create(attestations_to_create)
            
        return {'type': 'ir.actions.act_window_close'}
