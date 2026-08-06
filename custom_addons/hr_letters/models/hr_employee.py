from odoo import api, fields, models, _
import base64


DEFAULT_PRIMARY = '#000000'
DEFAULT_SECONDARY = '#000000'


# class IrActionsReport(models.Model):
#     _inherit = 'ir.actions.actions'
#
#     @api.model
#     def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
#         print('KESHAV------------------')
#         # Your custom logic goes here
#         # You can access the original method using super() if needed
#         pdf_content = super(IrActionsReport, self)._render_qweb_pdf(res_ids=res_ids, data=data)
#
#         # Modify the result or add your own logic
#         if res_ids:
#
#             print("if k andar gya code====", res_ids)
#             report = self._get_report(report_ref)
#             print("report===============", report)
#             for res_id in res_ids:
#                 print("for k andar gya code=================", res_id)
#                 record = self.env[report.model].browse(res_id)
#                 print("record=====", record)
#                 print(record, '==========record')
#                 print(res_id, '==========res_id')
#
#                 # Save the PDF as an attachment to the record
#                 attachment_data = {
#                     'name': '%s.pdf' % report.name,
#                     'datas': pdf_content,
#                     'res_model': report.model,
#                     'res_id': res_id,
#                 }
#                 attachment = self.env['ir.attachment'].create(attachment_data)
#
#                 # Post a message to the record
#                 message = "PDF has been downloaded for record with %s" % report.name
#                 record.message_post(body=message, attachment_ids=[attachment.id])
#         return pdf_content, 'pdf'


class HREmployee(models.Model):
    _inherit = "hr.employee"

    joining_date = fields.Date(string="Date of Joining")
    effective_date = fields.Date(string="Effective Date")
    resignation_date = fields.Date(string="Resignation  Date")
    date = fields.Date(string="Today Date",  default=fields.Date.context_today)
    annually_salary = fields.Float(string="Annually Salary")

    def action_appraisal_letter(self):
        template_id = self.env.ref('hr_letters.email_template_appraisal_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)

        appraisal_report = self.env.ref('hr_letters.action_appraisal_letter_report')
        data_record = base64.b64encode(self.env['ir.actions.report'].sudo()._render_qweb_pdf(appraisal_report, [self.id], data=None)[0])
        ir_values = {
            'name': 'Appraisal Letter',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.applicant',
        }
        appraisal_report_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.employee',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            'default_attachment_ids': [(4, appraisal_report_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_experience_letter(self):
        template_id = self.env.ref('hr_letters.email_template_experience_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)

        experience_report = self.env.ref('hr_letters.action_experience_letter_report')
        data_record = base64.b64encode(
            self.env['ir.actions.report'].sudo()._render_qweb_pdf(experience_report, [self.id], data=None)[0])
        ir_values = {
            'name': 'Experience Letter',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.applicant',
        }
        experience_report_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.employee',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            'default_attachment_ids': [(4, experience_report_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_resignation_letter(self):
        template_id = self.env.ref('hr_letters.email_template_resignation_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)

        resignation_report = self.env.ref('hr_letters.action_resignation_letter_report')
        data_record = base64.b64encode(
            self.env['ir.actions.report'].sudo()._render_qweb_pdf(resignation_report, [self.id], data=None)[0])
        ir_values = {
            'name': 'Resignation Letter',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.applicant',
        }
        resignation_report_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.employee',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            'default_attachment_ids': [(4, resignation_report_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_appointment_letter(self):
        template_id = self.env.ref('hr_letters.email_template_appointment_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)

        # Render the appointment letter report and create an attachment
        appointment_report = self.env.ref('hr_letters.action_appointment_letter_report')
        data_record = base64.b64encode(self.env['ir.actions.report'].sudo()._render_qweb_pdf(appointment_report, [self.id], data=None)[0])
        ir_values = {
            'name': 'Appointment Letter',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.applicant',
        }
        appointment_report_attachment = self.env['ir.attachment'].sudo().create(ir_values)

        # Compose the email using the mail template
        ctx = {
            'default_model': 'hr.employee',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            'default_attachment_ids': [(4, appointment_report_attachment.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        # Attach the appointment letter report to the chatter
        # self.message_post(
        #     body=_("Appointment Letter has been sent."),
        #     attachment_ids=[appointment_report_attachment.id],
        #     subject=_("Appointment Letter"),
        # )

    def action_relieving_letter(self):
        template_id = self.env.ref('hr_letters.email_template_relieving_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)

        relieving_report = self.env.ref('hr_letters.action_reliving_letter_report')
        data_record = base64.b64encode(self.env['ir.actions.report'].sudo()._render_qweb_pdf(relieving_report, [self.id], data=None)[0])
        ir_values = {
            'name': 'Relieving Letter',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.applicant',
        }
        relieving_report_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.employee',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            'default_attachment_ids': [(4, relieving_report_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_promotion_letter(self):
        template_id = self.env.ref('hr_letters.email_template_promotion_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)

        relieving_report = self.env.ref('hr_letters.action_promotion_letter_report')
        data_record = base64.b64encode(self.env['ir.actions.report'].sudo()._render_qweb_pdf(relieving_report, [self.id], data=None)[0])
        ir_values = {
            'name': 'Relieving Letter',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.applicant',
        }
        relieving_report_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.employee',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            'default_attachment_ids': [(4, relieving_report_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class HRApplicant(models.Model):
    _inherit = "hr.applicant"

    location = fields.Many2one('hr.work.location', string="Job Location")


    def action_offer_letter(self):
        template_id = self.env.ref('hr_letters.email_template_offer_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)
        offer_letter_rpt_id = self.env.ref('hr_letters.action_offer_letter_report')
        data_record = base64.b64encode(self.env['ir.actions.report'].sudo()._render_qweb_pdf(offer_letter_rpt_id, [self.id], data=None)[0])
        ir_values = {
            'name': 'Offer Letter',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.applicant',
        }
        offer_letter_rpt_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.applicant',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            'default_attachment_ids': [(4, offer_letter_rpt_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_send_email_letter(self):
        template_id = self.env.ref('hr_letters.email_template_send_email').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)
        offer_letter_rpt_id = self.env.ref('hr_letters.template_rpt_send_email_view')
        # data_record = base64.b64encode(self.env['ir.actions.report'].sudo()._render_qweb_pdf(offer_letter_rpt_id, [self.id], data=None)[0])
        # ir_values = {
        #     'name': 'Send Document Email',
        #     'type': 'binary',
        #     'datas': data_record,
        #     'store_fname': data_record,
        #     'mimetype': 'application/pdf',
        #     'res_model': 'hr.applicant',
        # }
        # offer_letter_rpt_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.applicant',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            # 'default_attachment_ids': [(4, offer_letter_rpt_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_send_email_joining(self):
        template_id = self.env.ref('hr_letters.email_template_joining_letter').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        template = self.env['mail.template'].browse(template_id)
        offer_letter_rpt_id = self.env.ref('hr_letters.template_rpt_joining_email_view')
        # data_record = base64.b64encode(self.env['ir.actions.report'].sudo()._render_qweb_pdf(offer_letter_rpt_id, [self.id], data=None)[0])
        # ir_values = {
        #     'name': 'Joining Letter',
        #     'type': 'binary',
        #     'datas': data_record,
        #     'store_fname': data_record,
        #     'mimetype': 'application/pdf',
        #     'res_model': 'hr.applicant',
        # }
        # offer_letter_rpt_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        ctx = {
            'default_model': 'hr.applicant',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': False,
            # 'default_attachment_ids': [(4, offer_letter_rpt_attachment_id.id)]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # @api.model
    # def _default_external_letter_layout_id(self):
    #     # Replace 'your_module.external_layout_letters' with the actual path to your view
    #     view_id = self.env['ir.ui.view'].search([('name', '=', 'external_layout_letters'), ('type', '=', 'qweb')], limit=1)
    #     print('fffffffffff', view_id)
    #     return view_id.id if view_id else False

    external_letter_layout_id = fields.Many2one("ir.ui.view", string="External Letter Layout")

    # @api.model
    # def _prepare_report_view_action(self, template):
    #     template_id = self.env.ref(template)
    #     print('---template-id---', template_id)
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'ir.ui.view',
    #         'view_mode': 'form',
    #         'res_id': template_id.id,
    #     }

    def edit_custom_external_header(self):
        if not self.external_letter_layout_id:
            return False

        return {
            'name': 'External Letter Layout View',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.ui.view',
            'view_mode': 'form',
            'res_id': self.external_letter_layout_id.id,
        }

    # def edit_external_header(self):
    #     print('Edit Button--')
    #     if not self.external_letter_layout_id:
    #         return False
    #     return self._prepare_report_view_action(self.external_letter_layout_id.key)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(external_letter_layout_id=int(self.env['ir.config_parameter'].sudo().get_param('hr_letters.external_letter_layout_id', False)),)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('hr_letters.external_letter_layout_id', self.external_letter_layout_id.id or False)


class ResCompany(models.Model):
    _inherit = "res.company"

    external_letter_layout_id = fields.Many2one('ir.ui.view', 'HR Letters Template')

class HREmployee(models.Model):
    _inherit = "hr.job"

    notice_period = fields.Char(string="Notice Period")




# class BaseDocumentLayout(models.TransientModel):
#     _inherit = "base.document.layout"
#
#     external_letter_layout_id = fields.Many2one(related='company_id.external_letter_layout_id', readonly=False)
#     letter_layout_id = fields.Many2one('report.layout')

    # @api.onchange('company_id')
    # def _onchange_company_id(self):
    #     for wizard in self:
    #         wizard.logo = wizard.company_id.logo
    #         wizard.report_header = wizard.company_id.report_header
    #         # company_details and report_footer can store empty strings (set by the user) or false (meaning the user didn't set a value). Since both are falsy values, we use isinstance of string to differentiate them
    #         wizard.report_footer = wizard.company_id.report_footer if isinstance(wizard.company_id.report_footer,
    #                                                                              str) else wizard.report_footer
    #         wizard.company_details = wizard.company_id.company_details if isinstance(wizard.company_id.company_details,
    #                                                                                  str) else wizard.company_details
    #         wizard.paperformat_id = wizard.company_id.paperformat_id
    #         wizard.external_letter_layout_id = wizard.company_id.external_letter_layout_id
    #         print('hhhhhhhhhhh', wizard.external_letter_layout_id)
    #         wizard.font = wizard.company_id.font
    #         wizard.primary_color = wizard.company_id.primary_color
    #         wizard.secondary_color = wizard.company_id.secondary_color
    #         wizard_layout = wizard.env["report.layout"].search([('view_id.key', '=', wizard.company_id.external_letter_layout_id.key)])
    #         print('==========', wizard_layout)
    #         wizard.letter_layout_id = wizard_layout or wizard_layout.search([], limit=1)
    #
    #         if not wizard.primary_color:
    #             wizard.primary_color = wizard.logo_primary_color or DEFAULT_PRIMARY
    #         if not wizard.secondary_color:
    #             wizard.secondary_color = wizard.logo_secondary_color or DEFAULT_SECONDARY

    # @api.onchange('letter_layout_id')
    # def _onchange_letter_layout_id(self):
    #     for wizard in self:
    #         wizard.external_letter_layout_id = wizard.letter_layout_id.view_id
    #         print('vvvvvvvvvvvvv', wizard.external_letter_layout_id)
