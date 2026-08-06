# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError

class ConstructionDailyLog(models.Model):
    _name = 'construction.daily.log'
    _description = 'Construction Daily Progress Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Log Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New Log'))
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    lifecycle_id = fields.Many2one('construction.lifecycle', related='project_id.lifecycle_id', store=True)
    job_order_id = fields.Many2one('construction.job.order', string='Work Order', domain="[('project_id', '=', project_id)]", tracking=True)
    phase_id = fields.Many2one('construction.phase', string='Phase', domain="[('lifecycle_id', '=', lifecycle_id)]", tracking=True)
    supervisor_id = fields.Many2one('res.users', string='Supervisor', default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted')
    ], string='Status', default='draft', tracking=True)
    
    labor_count = fields.Integer(string='Total Labor Count on Site', compute='_compute_labor_count', store=True)
    skilled_labor_count = fields.Integer(string='Skilled Labor', tracking=True)
    unskilled_labor_count = fields.Integer(string='Unskilled Labor', tracking=True)
    
    weather_conditions = fields.Selection([
        ('sunny', 'Sunny / Clear'),
        ('cloudy', 'Cloudy'),
        ('rain', 'Rain'),
        ('snow', 'Snow / Extreme')
    ], string='Weather Conditions')
    
    equipment_notes = fields.Html(string='Equipment Usage Notes')
    issues_notes = fields.Html(string='Issues / Delays')
    consumption_ids = fields.One2many('construction.job.consumption.line', 'daily_log_id', string='Material Consumption')
    
    allowed_product_ids = fields.Many2many('product.product', compute='_compute_allowed_products')

    @api.onchange('job_order_id', 'project_id', 'date')
    def _onchange_log_identity(self):
        if self.job_order_id:
            self.project_id = self.job_order_id.project_id
            self.phase_id = self.job_order_id.phase_id
        
        # Real-time preview with native sequence placeholder
        if self.project_id and self.date:
            self.name = f"{self.project_id.name} - {self.date} - ####"
        else:
            self.name = _("New Log")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New Log') == 'New Log' or not vals.get('name'):
                project = self.env['project.project'].browse(vals.get('project_id'))
                date = vals.get('date') or fields.Date.context_today(self)
                if project and date:
                    seq = self.env['ir.sequence'].next_by_code('construction.daily.log') or '0000'
                    vals['name'] = f"{project.name} - {date} - {seq}"
        return super().create(vals_list)

    @api.depends('job_order_id', 'job_order_id.material_plan_ids')
    def _compute_allowed_products(self):
        for log in self:
            if log.job_order_id:
                log.allowed_product_ids = log.job_order_id.material_plan_ids.mapped('product_id')
            else:
                log.allowed_product_ids = self.env['product.product']

    def action_submit(self):
        for record in self:
            record.state = 'submitted'
            
            # 1. Budget Breach Detection
            over_consumed_items = []
            if record.job_order_id:
                for cons_line in record.consumption_ids:
                    # Find matching plan line in Job Order
                    plan_line = record.job_order_id.material_plan_ids.filtered(lambda p: p.product_id == cons_line.product_id)
                    if plan_line:
                        # Since consumed_qty is a stored compute field, it might not be updated yet in the same transaction
                        # So we search directly
                        total_consumed_for_product = sum(self.env['construction.job.consumption.line'].search([
                            ('job_order_id', '=', record.job_order_id.id),
                            ('product_id', '=', cons_line.product_id.id)
                        ]).mapped('quantity'))
                        
                        if total_consumed_for_product > plan_line[0].quantity:
                            over_consumed_items.append(f"{cons_line.product_id.name} (Plan: {plan_line[0].quantity}, Actual: {total_consumed_for_product})")

            # 2. PM Notifications
            if record.project_id.user_id:
                summary = _('Daily Log Submitted: %s') % record.name
                note = _('Site supervisor %s has submitted a daily log for project %s.') % (record.supervisor_id.name, record.project_id.name)
                
                # Upgrade summary if breach detected
                if over_consumed_items:
                    summary = _('[BUDGET ALERT] Over-consumption in Log: %s') % record.name
                    note += _('\n\nWARNING: The following materials have exceeded their planned budget:\n- %s') % '\n- '.join(over_consumed_items)
                
                record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=record.project_id.user_id.id,
                    summary=summary,
                    note=note
                )
            
            # 3. Chatter Warning
            log_msg = _("Site Log has been submitted and locked for review.")
            if over_consumed_items:
                record.message_post(body=log_msg)

    visitor_ids = fields.One2many('construction.site.visitor', 'daily_log_id', string='Site Visitors')
    image_ids = fields.One2many('construction.daily.log.image', 'daily_log_id', string='Progress Photos')

    @api.depends('skilled_labor_count', 'unskilled_labor_count')
    def _compute_labor_count(self):
        for log in self:
            log.labor_count = log.skilled_labor_count + log.unskilled_labor_count

    def write(self, vals):
        for record in self:
            if record.state == 'submitted' and any(f not in ['state'] for f in vals):
                raise UserError(_("Submitted Daily Logs are locked and cannot be modified."))
        return super(ConstructionDailyLog, self).write(vals)

    def unlink(self):
        for record in self:
            if record.state == 'submitted':
                raise UserError(_("Submitted Daily Logs cannot be deleted to preserve site history."))
        return super(ConstructionDailyLog, self).unlink()


class ConstructionSiteVisitor(models.Model):
    _name = 'construction.site.visitor'
    _description = 'Site Visitor Registry'

    daily_log_id = fields.Many2one('construction.daily.log', string='Daily Log', ondelete='cascade')
    name = fields.Char(string='Visitor Name', required=True)
    company = fields.Char(string='Company / Organization')
    reason = fields.Char(string='Reason for Visit')
    time_in = fields.Float(string='Time In')
    time_out = fields.Float(string='Time Out')

    @api.depends('daily_log_id.date', 'daily_log_id.project_id')
    def _compute_name(self):
        for visitor in self:
            if visitor.daily_log_id.date and visitor.daily_log_id.project_id:
                visitor.name = f"Visitor: {visitor.name} - {visitor.daily_log_id.date}"
            else:
                visitor.name = visitor.name or "New Visitor"


class ConstructionDailyLogImage(models.Model):
    _name = 'construction.daily.log.image'
    _description = 'Daily Log Progress Image'

    name = fields.Char("Title", required=True)
    daily_log_id = fields.Many2one('construction.daily.log', "Daily Log", required=True, ondelete='cascade')
    image = fields.Image("Image", max_width=1920, max_height=1920, required=True)
    date = fields.Date("Date Taken", default=fields.Date.context_today)
    notes = fields.Text("Description")
