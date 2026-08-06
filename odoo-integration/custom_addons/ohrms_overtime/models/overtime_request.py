# -- coding: utf-8 --
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from dateutil import relativedelta
from datetime import timedelta
import pandas as pd
import pytz
# pyrefly: ignore [missing-import]
from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError, ValidationError
# pyrefly: ignore [missing-import]
from odoo.addons.resource.models.resource import Intervals
HOURS_PER_DAY = 8.0


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    primary_ot_type = fields.Selection([
        ('holiday', 'Holiday'),
        ('weekend', 'Weekend'),
        ('night', 'Night'),
        ('normal', 'Normal'),
        ('none', 'None')
    ], compute='_compute_primary_ot_type', string="OT Type")

    def _compute_primary_ot_type(self):
        public_holidays = self.env['resource.calendar.leaves'].search([('resource_id', '=', False)])
        holiday_dates = set()
        for leave in public_holidays:
            d = leave.date_from.date()
            while d <= leave.date_to.date():
                holiday_dates.add(d)
                d += timedelta(days=1)
                
        for att in self:
            att.primary_ot_type = 'none'
            if not att.check_in or not att.check_out:
                continue
                
            tz_name = att.employee_id.tz or self.env.user.tz or 'UTC'
            tz = pytz.timezone(tz_name)
            local_dt = att.check_in.replace(tzinfo=pytz.utc).astimezone(tz)
            effective_date = (local_dt - timedelta(hours=6)).date()
            
            if effective_date in holiday_dates:
                att.primary_ot_type = 'holiday'
            elif effective_date.weekday() in [5, 6]:
                att.primary_ot_type = 'weekend'
            elif local_dt.hour >= 22 or local_dt.hour < 6:
                att.primary_ot_type = 'night'
            else:
                att.primary_ot_type = 'normal'

class HrOverTime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread']

    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.onchange('days_no_tmp')
    def _onchange_days_no_tmp(self):
        self.days_no = self.days_no_tmp

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id, required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User",
                                   related='employee_id.user_id',
                                   default=lambda self: self.env.uid,
                                   store=True)
    current_user_boolean = fields.Boolean()
    project_id = fields.Many2one('project.project', string="Project")
    project_manager_id = fields.Many2one('res.users', string="Project Manager")
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id",
                                  )
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date to')
    days_no_tmp = fields.Float('Hours', compute="_get_days", store=True)
    days_no = fields.Float('No. of Days', store=True)
    desc = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'),
                              ('f_approve', 'Waiting'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused')], string="state",
                             default="draft")
    cancel_reason = fields.Text('Refuse Reason')
    leave_id = fields.Many2one('hr.leave.allocation',
                               string="Leave ID")
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name')
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="leave", required=True, string="Type")
    overtime_type_id = fields.Many2one('overtime.type', domain="[('type','=',type),('duration_type','=', "
                                                               "duration_type)]")
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.Many2many('hr.attendance', string='Attendance')
    work_schedule = fields.One2many(
        related='employee_id.resource_calendar_id.attendance_ids')
    global_leaves = fields.One2many(
        related='employee_id.resource_calendar_id.global_leave_ids')
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)

    ot_normal_hours = fields.Float('Normal OT Hours', compute='_compute_overtime_buckets', store=True)
    ot_normal_amount = fields.Float('Normal OT Amount', compute='_compute_overtime_buckets', store=True)
    
    ot_night_hours = fields.Float('Night OT Hours', compute='_compute_overtime_buckets', store=True)
    ot_night_amount = fields.Float('Night OT Amount', compute='_compute_overtime_buckets', store=True)
    
    ot_weekend_hours = fields.Float('Weekend OT Hours', compute='_compute_overtime_buckets', store=True)
    ot_weekend_amount = fields.Float('Weekend OT Amount', compute='_compute_overtime_buckets', store=True)
    
    ot_holiday_hours = fields.Float('Holiday OT Hours', compute='_compute_overtime_buckets', store=True)
    ot_holiday_amount = fields.Float('Holiday OT Amount', compute='_compute_overtime_buckets', store=True)
    
    ot_total_amount = fields.Float('Total OT Amount', compute='_compute_overtime_buckets', store=True)

    def _reset_buckets(self):
        self.update({
            'ot_normal_hours': 0, 'ot_normal_amount': 0,
            'ot_night_hours': 0, 'ot_night_amount': 0,
            'ot_weekend_hours': 0, 'ot_weekend_amount': 0,
            'ot_holiday_hours': 0, 'ot_holiday_amount': 0,
            'ot_total_amount': 0, 'cash_hrs_amount': 0
        })

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_overlap(self):
        for req in self:
            if not req.date_from or not req.date_to or not req.employee_id:
                continue
            
            domain = [
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', '!=', 'refused'),
                ('date_from', '<', req.date_to),
                ('date_to', '>', req.date_from)
            ]
            overlapping_reqs = self.search(domain)
            if overlapping_reqs:
                raise ValidationError(_('You cannot create overlapping overtime requests for the same employee.'))

    @api.depends('date_from', 'date_to', 'employee_id', 'contract_id.dynamic_hourly_rate')
    def _compute_overtime_buckets(self):
        for req in self:
            if not req.date_from or not req.date_to or not req.employee_id or not req.contract_id:
                req._reset_buckets()
                continue
                
            tz_name = req.employee_id.tz or self.env.user.tz or 'UTC'
            tz = pytz.timezone(tz_name)
            
            # Since widget="date" saves as 00:00:00, we make date_to inclusive of the whole day (23:59:59)
            inclusive_date_to = req.date_to + timedelta(hours=23, minutes=59, seconds=59)
            
            domain = [
                ('employee_id', '=', req.employee_id.id),
                ('check_in', '<', inclusive_date_to),
                '|', ('check_out', '=', False), ('check_out', '>', req.date_from)
            ]
            if 'state' in self.env['hr.attendance']._fields:
                domain.insert(2, ('state', '=', 'approved'))
            
            attendances = self.env['hr.attendance'].search(domain)
            
            holiday_dates = set()
            if req.employee_id.resource_calendar_id:
                for leave in req.employee_id.resource_calendar_id.global_leave_ids:
                    if not leave.date_from or not leave.date_to:
                        continue
                    l_start = leave.date_from.replace(tzinfo=pytz.utc).astimezone(tz).date()
                    l_end = leave.date_to.replace(tzinfo=pytz.utc).astimezone(tz).date()
                    d = l_start
                    while d <= l_end:
                        holiday_dates.add(d)
                        d += timedelta(days=1)
            
            calendar = req.employee_id.resource_calendar_id
            start_dt = pytz.utc.localize(req.date_from)
            end_dt = pytz.utc.localize(inclusive_date_to)
            
            if calendar:
                work_intervals = calendar._work_intervals_batch(start_dt, end_dt, resources=req.employee_id.resource_id)[req.employee_id.resource_id.id]
            else:
                work_intervals = Intervals([])
                
            att_intervals_list = []
            for att in attendances:
                if not att.check_out:
                    continue
                start_utc = max(req.date_from, att.check_in)
                end_utc = min(inclusive_date_to, att.check_out)
                if start_utc >= end_utc:
                    continue
                att_intervals_list.append((pytz.utc.localize(start_utc), pytz.utc.localize(end_utc), att))
                
            attendance_intervals = Intervals(att_intervals_list)
            overtime_intervals = attendance_intervals - work_intervals
            
            norm_hrs = night_hrs = week_hrs = hol_hrs = 0.0
            
            for start_aware, end_aware, att in overtime_intervals:
                current = start_aware.replace(tzinfo=None)
                end_naive = end_aware.replace(tzinfo=None)
                
                while current < end_naive:
                    chunk_end = min(current + timedelta(minutes=1), end_naive)
                    chunk_duration = (chunk_end - current).total_seconds() / 3600.0
                    
                    local_dt = current.replace(tzinfo=pytz.utc).astimezone(tz)
                    effective_date = (local_dt - timedelta(hours=6)).date()
                    
                    is_holiday = effective_date in holiday_dates
                    is_weekend = effective_date.weekday() in [5, 6]
                    is_night = local_dt.hour >= 22 or local_dt.hour < 6
                    
                    if is_holiday:
                        hol_hrs += chunk_duration
                    elif is_weekend:
                        week_hrs += chunk_duration
                    elif is_night:
                        night_hrs += chunk_duration
                    else:
                        norm_hrs += chunk_duration
                        
                    current = chunk_end
            
            rate = req.contract_id.dynamic_hourly_rate
            norm_amt = norm_hrs * rate * 1.5
            night_amt = night_hrs * rate * 1.75
            week_amt = week_hrs * rate * 2.0
            hol_amt = hol_hrs * rate * 2.5
            tot_amt = norm_amt + night_amt + week_amt + hol_amt
            
            req.update({
                'ot_normal_hours': norm_hrs, 'ot_normal_amount': norm_amt,
                'ot_night_hours': night_hrs, 'ot_night_amount': night_amt,
                'ot_weekend_hours': week_hrs, 'ot_weekend_amount': week_amt,
                'ot_holiday_hours': hol_hrs, 'ot_holiday_amount': hol_amt,
                'ot_total_amount': tot_amt,
                'cash_hrs_amount': tot_amt  # Keep for backward compatibility
            })

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                })

    @api.depends('project_id')
    def _get_project_manager(self):
        for sheet in self:
            if sheet.project_id:
                sheet.update({
                    'project_manager_id': sheet.project_id.user_id.id,
                })

    @api.depends('date_from', 'date_to')
    def _get_days(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError('Start Date must be less than End Date')
        for sheet in self:
            if sheet.date_from and sheet.date_to:
                start_dt = fields.Datetime.from_string(sheet.date_from)
                finish_dt = fields.Datetime.from_string(sheet.date_to)
                s = finish_dt - start_dt
                difference = relativedelta.relativedelta(finish_dt, start_dt)
                hours = difference.hours
                minutes = difference.minutes
                days_in_mins = s.days * 24 * 60
                hours_in_mins = hours * 60
                days_no = ((days_in_mins + hours_in_mins + minutes) / (24 * 60))

                diff = sheet.date_to - sheet.date_from
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                sheet.update({
                    'days_no_tmp': hours if sheet.duration_type == 'hours' else days_no,
                })

    @api.onchange('overtime_type_id')
    def _get_hour_amount(self):
        if self.overtime_type_id.rule_line_ids and self.duration_type == 'hours':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_hour:
                        cash_amount = self.contract_id.over_hour * recd.hrs_amount
                        self.cash_hrs_amount = cash_amount
                    else:
                        raise UserError(_("Hour Overtime Needs Hour Wage in Employee Contract."))
        elif self.overtime_type_id.rule_line_ids and self.duration_type == 'days':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_day:
                        cash_amount = self.contract_id.over_day * recd.hrs_amount
                        self.cash_day_amount = cash_amount
                    else:
                        raise UserError(_("Day Overtime Needs Day Wage in Employee Contract."))


    def submit_to_f(self):
        # notification to employee
        recipient_partners = [(4, self.current_user.partner_id.id)]
        body = "Your OverTime Request Waiting Finance Approve .."
        msg = _(body)

        # notification to finance :
        group = self.env.ref('account.group_account_invoice', False)
        recipient_partners = []

        body = "You Get New Time in Lieu Request From Employee : " + str(
            self.employee_id.name)
        msg = _(body)
        return self.sudo().write({
            'state': 'f_approve'
        })

    def approve(self):
        if self.overtime_type_id.type == 'leave':
            total_ot_hours = self.ot_normal_hours + self.ot_night_hours + self.ot_weekend_hours + self.ot_holiday_hours
            allocation_days = total_ot_hours / HOURS_PER_DAY
            
            holiday_vals = {
                'name': 'Overtime',
                'holiday_status_id': self.overtime_type_id.leave_type.id,
                'number_of_days': allocation_days,
                'notes': self.desc,
                'holiday_type': 'employee',
                'employee_id': self.employee_id.id,
                'state': 'confirm',
            }
            holiday = self.env['hr.leave.allocation'].sudo().create(
                holiday_vals)
            self.leave_id = holiday.id

        # notification to employee :
        recipient_partners = [(4, self.current_user.partner_id.id)]
        body = "Your Time In Lieu Request Has been Approved ..."
        msg = _(body)
        self.sudo().write({
            'state': 'approved',
        })
        
        if self.overtime_type_id.type == 'leave' and self.leave_id:
            return {
                'name': _('Leave Allocation'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'hr.leave.allocation',
                'res_id': self.leave_id.id,
                'target': 'new',
            }

    def reject(self):

        self.state = 'refused'

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for req in self:
            domain = [
                ('date_from', '<=', req.date_to),
                ('date_to', '>=', req.date_from),
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', 'not in', ['refused']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_(
                    'You can not have 2 Overtime requests that overlaps on same day!'))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        return super(HrOverTime, self.sudo()).create(values)

    def unlink(self):
        for overtime in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete TIL request which is not in draft state.'))
        return super(HrOverTime, self).unlink()

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_date(self):
        holiday = False
        if self.contract_id and self.date_from and self.date_to:
            for leaves in self.contract_id.resource_calendar_id.global_leave_ids:
                leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
                overtime_dates = pd.date_range(self.date_from, self.date_to).date
                for over_time in overtime_dates:
                    for leave_date in leave_dates:
                        if leave_date == over_time:
                            holiday = True
            if holiday:
                self.write({
                    'public_holiday': 'You have Public Holidays in your Overtime request.'})
            else:
                self.write({'public_holiday': ' '})
            inclusive_date_to = self.date_to + timedelta(hours=23, minutes=59, seconds=59)
            domain = [
                ('check_in', '>=', self.date_from),
                ('check_in', '<=', inclusive_date_to),
                ('employee_id', '=', self.employee_id.id)
            ]
            if 'state' in self.env['hr.attendance']._fields:
                domain.insert(2, ('state', '=', 'approved'))
                
            hr_attendance = self.env['hr.attendance'].search(domain)
            
            filtered_attendances = self.env['hr.attendance']
            if self.employee_id.resource_calendar_id:
                calendar = self.employee_id.resource_calendar_id
                start_dt = pytz.utc.localize(self.date_from)
                end_dt = pytz.utc.localize(inclusive_date_to)
                work_intervals = calendar._work_intervals_batch(start_dt, end_dt, resources=self.employee_id.resource_id)[self.employee_id.resource_id.id]
                
                for att in hr_attendance:
                    if not att.check_out:
                        continue
                    att_start = pytz.utc.localize(max(self.date_from, att.check_in))
                    att_end = pytz.utc.localize(min(inclusive_date_to, att.check_out))
                    if att_start >= att_end:
                        continue
                        
                    att_interval = Intervals([(att_start, att_end, att)])
                    ot = att_interval - work_intervals
                    if ot:
                        filtered_attendances |= att
            else:
                filtered_attendances = hr_attendance
                
            self.update({
                'attendance_ids': [(6, 0, filtered_attendances.ids)]
            })


class HrOverTimeType(models.Model):
    _name = 'overtime.type'
    _description = "HR Overtime Type"

    name = fields.Char('Name')
    type = fields.Selection([('cash', 'Cash'),
                             ('leave', 'Leave ')])

    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type', domain="[('id', 'in', leave_compute)]")
    leave_compute = fields.Many2many('hr.leave.type', compute="_get_leave_type")
    rule_line_ids = fields.One2many('overtime.type.rule', 'type_line_id')

    @api.onchange('duration_type')
    def _get_leave_type(self):
        dur = ''
        ids = []
        if self.duration_type:
            if self.duration_type == 'days':
                dur = 'day'
            else:
                dur = 'hour'
            leave_type = self.env['hr.leave.type'].search([('request_unit', '=', dur)])
            for recd in leave_type:
                ids.append(recd.id)
            self.leave_compute = ids


class HrOverTimeTypeRule(models.Model):
    _name = 'overtime.type.rule'
    _description = "HR Overtime Type Rule"

    type_line_id = fields.Many2one('overtime.type', string='Over Time Type')
    name = fields.Char('Name', required=True)
    from_hrs = fields.Float('From', required=True)
    to_hrs = fields.Float('To', required=True)
    hrs_amount = fields.Float('Rate', required=True)