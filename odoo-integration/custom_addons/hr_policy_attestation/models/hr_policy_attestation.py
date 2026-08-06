# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrPolicyAttestation(models.Model):
    _name = 'hr.policy.attestation'
    _description = 'HR Policy Attestation'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    department_id = fields.Many2one(related='employee_id.department_id', store=True, readonly=True)
    
    version_id = fields.Many2one('hr.policy.version', string='Policy Version', required=True, ondelete='cascade')
    template_id = fields.Many2one(related='version_id.template_id', store=True, string='Policy Template', readonly=True)
    
    content_type = fields.Char(compute='_compute_content_type', readonly=True, string="Content Type")
    
    @api.depends('version_id.content_type')
    def _compute_content_type(self):
        for record in self:
            record.content_type = record.version_id.content_type
    body_html = fields.Html(related='version_id.body_html', readonly=True)
    attachment = fields.Binary(related='version_id.attachment', readonly=True)
    attachment_name = fields.Char(related='version_id.attachment_name', readonly=True)
    is_pdf = fields.Boolean(compute='_compute_is_pdf', string="Is PDF")

    @api.depends('attachment_name')
    def _compute_is_pdf(self):
        for record in self:
            record.is_pdf = False
            if record.attachment_name and record.attachment_name.lower().endswith('.pdf'):
                record.is_pdf = True

    status = fields.Selection([
        ('pending', 'Pending Action'),
        ('agreed', 'Agreed'),
        ('superseded', 'Superseded')
    ], string='Status', default='pending', required=True, tracking=True)
    
    signed_datetime = fields.Datetime(string='Signed Date & Time', readonly=True)
    ip_address = fields.Char(string='IP Address', readonly=True)
    user_agent = fields.Char(string='User Agent', readonly=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.template_id.name} - {record.employee_id.name}"
            result.append((record.id, name))
        return result

    def write(self, vals):
        # Prevent editing an agreed attestation
        for record in self:
            if record.status == 'agreed' and not self.env.context.get('allow_status_update'):
                if any(f in vals for f in ['status', 'signed_datetime', 'ip_address', 'user_agent', 'employee_id', 'version_id']):
                    raise UserError(_("You cannot modify an attestation that has already been agreed upon. This is a secure audit trail."))
        return super(HrPolicyAttestation, self).write(vals)

    def unlink(self):
        for record in self:
            if record.status == 'agreed':
                raise UserError(_("You cannot delete an attestation that has already been agreed upon."))
        return super(HrPolicyAttestation, self).unlink()

    def action_send_reminder(self):
        for record in self:
            if record.status == 'pending' and record.employee_id.user_id:
                # Send email
                template = self.env.ref('hr_policy_attestation.email_template_policy_reminder', raise_if_not_found=False)
                if template:
                    template.send_mail(record.id, force_send=True)
                
                # Send internal inbox message
                record.message_post(
                    body=_("Reminder: You have a pending HR policy document to review and sign: %s") % record.template_id.name,
                    partner_ids=[record.employee_id.user_id.partner_id.id],
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )

    def action_sign_document(self):
        for record in self:
            if record.status == 'pending' and record.employee_id.user_id.id == self.env.user.id:
                # Capture request context if available
                ip_address = False
                user_agent = False
                if hasattr(self.env.cr, 'httprequest') and self.env.cr.httprequest:
                    ip_address = self.env.cr.httprequest.remote_addr
                    user_agent = self.env.cr.httprequest.user_agent.string
                
                record.with_context(allow_status_update=True).write({
                    'status': 'agreed',
                    'signed_datetime': fields.Datetime.now(),
                    'ip_address': ip_address or 'Captured internally',
                    'user_agent': (user_agent[:255] if user_agent else 'Internal Odoo Client'),
                })

    @api.model
    def get_dashboard_data(self, *args, **kwargs):
        # Metrics
        total_policies = self.env['hr.policy.template'].search_count([])
        total_attestations = self.search_count([])
        agreed_count = self.search_count([('status', '=', 'agreed')])
        pending_count = self.search_count([('status', '=', 'pending')])
        
        compliance_rate = 0
        if total_attestations > 0:
            compliance_rate = round((agreed_count / total_attestations) * 100)

        # Chart Data: Group by Template and Status
        self.env.cr.execute("""
            SELECT t.name as template, a.status as status, COUNT(a.id) as count
            FROM hr_policy_attestation a
            JOIN hr_policy_version v ON a.version_id = v.id
            JOIN hr_policy_template t ON v.template_id = t.id
            GROUP BY t.name, a.status
        """)
        chart_raw = self.env.cr.dictfetchall()
        
        chart_data = {}
        for row in chart_raw:
            template = row['template']
            status = row['status']
            count = row['count']
            
            if template not in chart_data:
                chart_data[template] = {'agreed': 0, 'pending': 0, 'superseded': 0}
            chart_data[template][status] += count

        # Format for Chart.js
        labels = list(chart_data.keys())
        agreed_data = [chart_data[l]['agreed'] for l in labels]
        pending_data = [chart_data[l]['pending'] for l in labels]

        # Recent Signatures
        recent = self.search([('status', '=', 'agreed')], order='signed_datetime desc', limit=10)
        recent_list = []
        for r in recent:
            recent_list.append({
                'employee': r.employee_id.name,
                'policy': r.template_id.name,
                'date': r.signed_datetime.strftime("%Y-%m-%d %H:%M:%S") if r.signed_datetime else 'Unknown'
            })

        return {
            'metrics': {
                'total_policies': total_policies,
                'compliance_rate': compliance_rate,
                'pending_signatures': pending_count
            },
            'chart': {
                'labels': labels,
                'agreed': agreed_data,
                'pending': pending_data
            },
            'recent_signatures': recent_list
        }
