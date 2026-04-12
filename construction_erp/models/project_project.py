# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class Project(models.Model):
    _inherit = ['project.project', 'construction.notification.mixin']
    _name = 'project.project'

    location = fields.Char(string='Site Location')
    project_type = fields.Selection([
        ('construction', 'Construction'),
        ('soil_test', 'Soil Test'),
        ('design', 'Design'),
        ('inspection', 'Inspection')
    ], string='Project Type', tracking=True)
    site_manager_id = fields.Many2one('res.users', string='Site Manager', tracking=True)
    total_budget = fields.Monetary(string='Master Budget', currency_field='currency_id')
    total_estimated_aggregate = fields.Monetary(string='Aggregate Phase Estimates', compute='_compute_aggregate_estimations')
    total_expense = fields.Monetary(string='Total Expenses', compute='_compute_project_financials')
    total_collected = fields.Monetary(string='Total Collected', compute='_compute_project_financials')
    profitability = fields.Monetary(string='Net Profit / Loss', compute='_compute_project_financials')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    warehouse_id = fields.Many2one('stock.warehouse', string='Dedicated Site Warehouse', tracking=True)
    unit_ids = fields.One2many('real_estate.unit', 'project_id', string='Project Units')
    daily_log_ids = fields.One2many('construction.daily.log', 'project_id', string='Daily Logs')
    compliance_ids = fields.One2many('construction.compliance', 'project_id', string='Legal Document Ledger')
    progress_image_ids = fields.One2many('construction.project.image', 'project_id', string='Progress Photos')
    recent_image_ids = fields.Many2many('construction.project.image', compute='_compute_recent_images', string='Recent Site Visuals')
    project_image = fields.Image(string="Project Visual", max_width=1920, max_height=1920)
    unit_count = fields.Integer(compute='_compute_counts', string='Total Units')
    sold_unit_count = fields.Integer(compute='_compute_counts', string='Sold Units')
    unsold_unit_count = fields.Integer(compute='_compute_counts', string='Unsold / Available')
    total_sold_value = fields.Monetary(compute='_compute_sales_financials', string='Total Sales Value')
    total_collected_revenue = fields.Monetary(compute='_compute_sales_financials', string='Total Collected (Sales)')
    compliance_count = fields.Integer(compute='_compute_counts')
    expired_compliance_count = fields.Integer(compute='_compute_counts')
    daily_log_count = fields.Integer(compute='_compute_counts')
    consumption_count = fields.Integer(compute='_compute_counts')
    scrap_count = fields.Integer(compute='_compute_counts')
    estimate_count = fields.Integer(compute='_compute_counts')
    job_order_count = fields.Integer(compute='_compute_counts')
    document_count = fields.Integer(compute='_compute_counts')
    
    site_width = fields.Float(string='Site Width (m)')
    site_length = fields.Float(string='Site Length (m)')
    site_area = fields.Float(string='Total Area (sq.m)', compute='_compute_site_area', store=True)
    site_latitude = fields.Float(string='Latitude', digits=(10, 7))
    site_longitude = fields.Float(string='Longitude', digits=(10, 7))

    lifecycle_id = fields.Many2one('construction.lifecycle', string='Construction Life Cycle', tracking=True)
    current_phase_id = fields.Many2one('construction.phase', string='Current Phase', tracking=True, domain="[('lifecycle_id', '=', lifecycle_id)]")
    active_phase_job_count = fields.Integer(compute='_compute_active_phase_job_count', string='Pending Phase Jobs')
    phase_progress = fields.Float(compute='_compute_phase_progress', string='Cycle Progress (%)')
    job_order_ids = fields.One2many('construction.job.order', 'project_id', string='Project Job Orders')
    phase_config_ids = fields.One2many('project.phase.config', 'project_id', string='Phase Roadmap Configuration')
    roadmap_total_weight = fields.Float(compute='_compute_roadmap_total_weight', string='Roadmap Total Weight')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    is_final_phase = fields.Boolean(compute='_compute_is_final_phase', string='Is Final Lifecycle Phase')

    def action_start_project(self):
        for project in self:
            # Final validation of weights before starting
            total_weight = sum(project.phase_config_ids.mapped('weight'))
            if abs(total_weight - 100.0) > 0.01:
                raise models.ValidationError(_("Cannot start project '%s': The total phase weight must be exactly 100%%. Current total: %.2f%%.") % (project.name, total_weight))
            project.state = 'in_progress'

    @api.constrains('phase_config_ids', 'state')
    def _check_phase_roadmap_weights(self):
        for project in self:
            if project.state != 'draft' and project.phase_config_ids:
                total_weight = sum(project.phase_config_ids.mapped('weight'))
                if abs(total_weight - 100.0) > 0.01:
                    raise models.ValidationError(_("The total phase weight for project '%s' must be exactly 100%%. Currently, it is %.2f%%.") % (project.name, total_weight))

    def action_mark_done(self):
        for project in self:
            # Check if all phases are done (optional logic but useful)
            project.state = 'done'

    def action_cancel_project(self):
        for project in self:
            project.state = 'cancel'
    
    def action_create_job_order(self):
        self.ensure_one()
        return {
            'name': _('New Job Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.job.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_phase_id': self.current_phase_id.id,
            }
        }
    
    estimate_ids = fields.One2many('construction.estimate', 'project_id', string='Phase Estimates')
    estimate_line_ids = fields.Many2many('construction.estimate.line', compute='_compute_estimate_lines', string='Master Detailed Plan')

    @api.depends('site_width', 'site_length')
    def _compute_site_area(self):
        for project in self:
            project.site_area = project.site_width * project.site_length

    def _compute_estimate_lines(self):
        for project in self:
            project.estimate_line_ids = project.estimate_ids.mapped('line_ids')

    def _compute_aggregate_estimations(self):
        for project in self:
            aggregates = self.env['construction.estimate'].search([('project_id', '=', project.id)])
            project.total_estimated_aggregate = sum(aggregates.mapped('total_estimated_amount'))

    @api.depends('unit_ids.total_quantity', 'unit_ids.quantity_sold', 'estimate_ids', 'daily_log_ids', 'compliance_ids', 'job_order_ids.state', 'lifecycle_id')
    def _compute_counts(self):
        for project in self:
            project.estimate_count = self.env['construction.estimate'].search_count([('project_id', '=', project.id)])
            project.scrap_count = self.env['construction.scrap'].search_count([('project_id', '=', project.id)])
            project.daily_log_count = self.env['construction.daily.log'].search_count([('project_id', '=', project.id)])
            project.job_order_count = self.env['construction.job.order'].search_count([('project_id', '=', project.id)])
            project.document_count = self.env['construction.document'].search_count([('project_id', '=', project.id)])
            project.consumption_count = self.env['construction.consumption'].search_count([('project_id', '=', project.id)])
            
            # Unit counts from pooled totals
            units = project.unit_ids
            project.unit_count = sum(units.mapped('total_quantity'))
            project.sold_unit_count = sum(units.mapped('quantity_sold'))
            project.unsold_unit_count = project.unit_count - project.sold_unit_count
            
            project.compliance_count = len(project.compliance_ids)
            project.expired_compliance_count = len(project.compliance_ids.filtered(lambda c: c.status == 'expired'))
            project.active_phase_job_count = self.env['construction.job.order'].search_count([
                ('project_id', '=', project.id),
                ('phase_id', '=', project.current_phase_id.id),
                ('state', 'not in', ['completed', 'closed', 'cancelled'])
            ]) if project.current_phase_id else 0

    @api.depends('unit_ids.sale_order_ids.state', 'unit_ids.sale_order_ids.amount_total')
    def _compute_sales_financials(self):
        for project in self:
            confirmed_sales = self.env['sale.order'].search([
                ('project_id', '=', project.id),
                ('state', 'in', ['sale', 'done'])
            ])
            project.total_sold_value = sum(confirmed_sales.mapped('amount_total'))
            
            # Total Revenue Collected = Sum of fully paid installment amounts
            # related to the project unit pools
            installment_lines = self.env['real_estate.installment.line'].search([
                ('plan_id.sale_id.project_id', '=', project.id),
                ('is_invoiced', '=', True),
                ('invoice_id.payment_state', 'in', ['paid', 'in_payment'])
            ])
            project.total_collected_revenue = sum(installment_lines.mapped('amount'))

    @api.depends('phase_config_ids', 'phase_config_ids.contribution')
    def _compute_phase_progress(self):
        for project in self:
            if not project.lifecycle_id:
                project.phase_progress = 0.0
                continue
            
            # The project progress is now the total of individual phase contributions
            project.phase_progress = sum(project.phase_config_ids.mapped('contribution'))

    @api.depends('phase_config_ids.weight')
    def _compute_roadmap_total_weight(self):
        for project in self:
            project.roadmap_total_weight = sum(project.phase_config_ids.mapped('weight'))

    def _compute_recent_images(self):
        for project in self:
            project.recent_image_ids = self.env['construction.project.image'].search([
                ('project_id', '=', project.id)
            ], limit=5, order='date desc')

    total_committed_allocated = fields.Monetary(string='Committed Execution (JO)', compute='_compute_project_financials')
    
    # Variation Tracking KPIs
    variation_ids = fields.One2many('construction.variation.order', 'project_id', string='Variation Orders')
    total_variation_amount = fields.Monetary(string='Total Variations', compute='_compute_project_financials')
    revised_budget_amount = fields.Monetary(string='Revised Budget', compute='_compute_project_financials')

    def _compute_project_financials(self):
        for project in self:
            # 1. BOQ Baseline
            project.total_estimated_aggregate = sum(project.estimate_ids.mapped('total_estimated_amount'))
            
            # 2. Approved Budget (Master Cost Sheet)
            master_sheet = self.env['construction.cost.sheet'].search([('project_id', '=', project.id), ('state', '!=', 'draft')], limit=1)
            project.total_budget = master_sheet.total_cost if master_sheet else 0.0
            
            # 3. Variations
            approved_variations = project.variation_ids.filtered(lambda v: v.state == 'approved')
            project.total_variation_amount = sum(approved_variations.mapped('total_amount'))
            project.revised_budget_amount = project.total_budget + project.total_variation_amount
            
            # 4. Committed (Job Orders)
            project.total_committed_allocated = sum(project.job_order_ids.mapped('total_cost'))
            
            # 5. Actual Costs (From Pickings & Timesheets via Analytic Lines)
            if not project.analytic_account_id:
                project.total_expense = 0.0
                project.total_collected = 0.0
                project.profitability = 0.0
                continue
            
            analytic_lines = self.env['account.analytic.line'].search([('account_id', '=', project.analytic_account_id.id)])
            expenses = sum(line.amount for line in analytic_lines if line.amount < 0)
            collected = sum(line.amount for line in analytic_lines if line.amount > 0)
            
            project.total_expense = abs(expenses)
            project.total_collected = collected
            project.profitability = (project.revised_budget_amount - project.total_expense) if project.revised_budget_amount > 0 else (collected - abs(expenses))

    def action_view_variations(self):
        self.ensure_one()
        return {
            'name': _('Variation Orders: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'construction.variation.order',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_master_budget(self):
        self.ensure_one()
        cost_sheet = self.env['construction.cost.sheet'].search([('project_id', '=', self.id)], limit=1)
        if not cost_sheet:
            from odoo.exceptions import UserError
            raise UserError(_("No active budget (Cost Sheet) found for this project."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'construction.cost.sheet',
            'res_id': cost_sheet.id,
            'view_mode': 'form',
        }

    @api.depends('lifecycle_id', 'current_phase_id')
    def _compute_is_final_phase(self):
        for project in self:
            if not project.lifecycle_id or not project.current_phase_id:
                project.is_final_phase = False
                continue
            
            last_phase = self.env['construction.phase'].search([
                ('lifecycle_id', '=', project.lifecycle_id.id),
                ('active', '=', True)
            ], order='sequence desc', limit=1)
            
            project.is_final_phase = (project.current_phase_id.id == last_phase.id) if last_phase else False

    @api.model_create_multi
    def create(self, vals_list):
        projects = super(Project, self).create(vals_list)
        for project in projects:
            # Set default phase from selected Life Cycle if not already set
            if project.lifecycle_id and not project.current_phase_id:
                default_phase = self.env['construction.phase'].search([
                    ('lifecycle_id', '=', project.lifecycle_id.id),
                    ('active', '=', True)
                ], order='sequence asc', limit=1)
                if default_phase:
                    project.current_phase_id = default_phase.id
                
            if not project.warehouse_id:
                safe_code = (project.name[:3] if project.name else "PRJ").upper()
                warehouse = self.env['stock.warehouse'].create({
                    'name': f"{project.name} Warehouse",
                    'code': f"{safe_code}{project.id}"
                })
                project.warehouse_id = warehouse.id

            if not project.analytic_account_id:
                analytic_account = self.env['account.analytic.account'].create({
                    'name': project.name,
                    'partner_id': project.partner_id.id,
                    'company_id': project.company_id.id,
                })
                project.analytic_account_id = analytic_account.id
                
            # Initialize Phase Weights from Lifecycle template
            if project.lifecycle_id and not project.phase_config_ids:
                for phase in project.lifecycle_id.phase_ids:
                    self.env['project.phase.config'].create({
                        'project_id': project.id,
                        'phase_id': phase.id,
                        'weight': phase.weight
                    })
        return projects

    def write(self, vals):
        res = super(Project, self).write(vals)
        if 'lifecycle_id' in vals:
            for project in self:
                # Refresh phase configurations if lifecycle changes
                # (Optional: only if empty? Usually safest to just add missing or reset)
                existing_phases = project.phase_config_ids.mapped('phase_id').ids
                new_phases = project.lifecycle_id.phase_ids
                for lp in new_phases:
                    if lp.id not in existing_phases:
                        self.env['project.phase.config'].create({
                            'project_id': project.id,
                            'phase_id': lp.id,
                            'weight': lp.weight
                        })
        return res

    def action_sync_roadmap(self):
        """ Force synchronization of all phases from the assigned lifecycle template """
        for project in self:
            if not project.lifecycle_id:
                continue
            
            existing_phases = project.phase_config_ids.mapped('phase_id').ids
            new_phases = project.lifecycle_id.phase_ids
            
            # Add missing phases
            for lp in new_phases:
                if lp.id not in existing_phases:
                    self.env['project.phase.config'].create({
                        'project_id': project.id,
                        'phase_id': lp.id,
                        'weight': lp.weight
                    })
            
            self.message_post(body=_("Site Roadmap Synchronized: All lifecycle phases have been initialized."))

    def action_advance_phase(self):
        from odoo.exceptions import UserError
        for project in self:
            if project.state != 'in_progress':
                raise UserError(_("Phase advancement is only permitted while the project is 'In Progress'. Current status: %s") % project.state)

            if not project.current_phase_id:
                # If no phase, try to set the first one of the lifecycle
                if project.lifecycle_id:
                    first_phase = self.env['construction.phase'].search([
                        ('lifecycle_id', '=', project.lifecycle_id.id),
                        ('active', '=', True)
                    ], order='sequence asc', limit=1)
                    if first_phase:
                        project.current_phase_id = first_phase.id
                        continue
                raise UserError(_("No current phase or lifecycle defined for this project."))

            # 1. Check for incomplete job orders in the current phase
            phase_jobs = self.env['construction.job.order'].search([
                ('project_id', '=', project.id),
                ('phase_id', '=', project.current_phase_id.id),
            ])
            if not phase_jobs:
                 raise UserError(_("Phase advancement restricted: At least one Job Order must be executed and completed for phase '%s'.") % project.current_phase_id.name)

            incomplete_jobs = phase_jobs.filtered(lambda j: j.state not in ['completed', 'closed', 'cancelled'])
            if incomplete_jobs:
                job_list = "\n".join(["- " + j.name for j in incomplete_jobs])
                raise UserError(_("Cannot advance phase. The following Job Orders for '%s' are still active:\n%s") % (project.current_phase_id.name, job_list))

            # New: Ensure all inspections passed in this phase
            failed_inspections = self.env['construction.inspection'].search([
                ('project_id', '=', project.id),
                ('phase_id', '=', project.current_phase_id.id),
                ('state', '!=', 'passed')
            ])
            if failed_inspections:
                 raise UserError(_("Cannot advance phase. There are pending or failed inspections for '%s'.") % project.current_phase_id.name)

            # 3. New: Quality Lock - Check for open NCRs
            open_ncrs = self.env['construction.ncr'].search([
                ('project_id', '=', project.id),
                ('state', 'not in', ['closed', 'void'])
            ])
            if open_ncrs:
                ncr_list = "\n".join(["- " + n.name for n in open_ncrs])
                raise UserError(_("Phase advancement blocked by Quality Control: The following Non-Conformance Reports (NCR) are still open:\n%s") % ncr_list)

            # 4. Find and set the next phase
            next_phase = self.env['construction.phase'].search([
                ('lifecycle_id', '=', project.lifecycle_id.id),
                ('active', '=', True),
                ('sequence', '>', project.current_phase_id.sequence)
            ], order='sequence asc', limit=1)
            
            if next_phase:
                # Move to next phase
                self.current_phase_id = next_phase.id
                self.message_post(body=_("Site Roadmap Advanced: Project is now in phase <b>%s</b>.") % next_phase.name)

                # Notify Site Manager/PM via WhatsApp/Telegram
                msg = _("Phase Advanced: %s\nProject: %s\nNew Phase: %s") % (self.name, self.name, next_phase.name)
                if self.site_manager_id:
                    self.notify_contact(self.site_manager_id, msg, title=_("Site Roadmap Update"))
                elif self.user_id:
                    self.notify_contact(self.user_id.partner_id, msg, title=_("Site Roadmap Update"))
                    
                # Notify active contractors
                active_contractors = self.job_order_ids.filtered(lambda jo: jo.state == 'active').mapped('contractor_id')
                for contractor in active_contractors:
                    self.notify_contact(contractor, msg, title=_("Site Status Update"))
            else:
                project.message_post(body=_("Project has reached the final phase of its lifecycle: <b>%s</b>") % project.current_phase_id.name)

    def action_open_real_estate_units(self):
        self.ensure_one()
        return {
            'name': 'Property Asset Inventory',
            'type': 'ir.actions.act_window',
            'res_model': 'real_estate.unit',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_open_sold_units(self):
        self.ensure_one()
        return {
            'name': 'Confirmed Sales & Contracts',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id), ('state', 'in', ['sale', 'done'])],
            'context': {'default_project_id': self.id},
        }

    def action_open_daily_logs(self):
        self.ensure_one()
        return {
            'name': 'Daily Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'construction.daily.log',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_open_active_phase_jobs(self):
        self.ensure_one()
        return {
            'name': _('Pending Job Orders: %s') % self.current_phase_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'construction.job.order',
            'view_mode': 'tree,form',
            'domain': [
                ('project_id', '=', self.id),
                ('phase_id', '=', self.current_phase_id.id),
                ('state', 'not in', ['completed', 'closed', 'cancelled'])
            ],
            'context': {
                'default_project_id': self.id,
                'default_phase_id': self.current_phase_id.id
            },
        }

    def action_open_compliance(self):
        self.ensure_one()
        return {
            'name': 'Compliance & Legal Permits',
            'type': 'ir.actions.act_window',
            'res_model': 'construction.compliance',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_open_job_orders(self):
        self.ensure_one()
        return {
            'name': 'Project Job Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'construction.job.order',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    # Procurement Intelligence
    procurement_risk_count = fields.Integer(compute='_compute_procurement_risk', string='Procurement Risks')
    total_ordered_amount = fields.Monetary(compute='_compute_procurement_financials', string='Total Ordered')
    total_delivered_amount = fields.Monetary(compute='_compute_procurement_financials', string='Total Delivered')

    def _compute_procurement_risk(self):
        for project in self:
            risks = self.env['construction.cost.material.line'].search([
                ('cost_sheet_id.project_id', '=', project.id),
                ('procurement_lead_time', '>', 0),
                ('quantity', '>', 0)
            ])
            # Logic: If planned qty is higher than ordered qty (implied by procurement state being not fully ordered)
            project.procurement_risk_count = len(risks.filtered(lambda r: r.actual_amount_spent == 0)) 

    def _compute_procurement_financials(self):
        for project in self:
            po_lines = self.env['purchase.order.line'].search([
                ('order_id.project_id', '=', project.id),
                ('state', 'in', ['purchase', 'done'])
            ])
            project.total_ordered_amount = sum(po_lines.mapped('price_subtotal'))
            project.total_delivered_amount = sum(l.qty_received * l.price_unit for l in po_lines)

    def action_view_procurement_risks(self):
        self.ensure_one()
        return {
            'name': _('Procurement Risks'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.cost.material.line',
            'view_mode': 'tree,form',
            'domain': [
                ('cost_sheet_id.project_id', '=', self.id),
                ('actual_amount_spent', '=', 0)
            ],
            'context': {'search_default_group_by_phase': 1}
        }

    def action_launch_sourcing_wizard(self):
        self.ensure_one()
        return {
            'name': _('Smart Sourcing (BOQ to PO)'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.purchase.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_phase_id': self.current_phase_id.id if self.current_phase_id else False,
            }
        }

    # Engineering Document Control
    rfi_count = fields.Integer(compute='_compute_engineering_counts', string='Pending RFIs')
    submittal_count = fields.Integer(compute='_compute_engineering_counts', string='Pending Submittals')

    def _compute_engineering_counts(self):
        for project in self:
            project.rfi_count = self.env['construction.rfi'].search_count([
                ('project_id', '=', project.id),
                ('state', '=', 'sent')
            ])
            project.submittal_count = self.env['construction.submittal'].search_count([
                ('project_id', '=', project.id),
                ('approval_status', '=', 'pending')
            ])

    def action_view_project_rfis(self):
        self.ensure_one()
        return {
            'name': _('Requests for Information (RFI)'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.rfi',
            'view_mode': 'kanban,tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id}
        }

    def action_view_project_submittals(self):
        self.ensure_one()
        return {
            'name': _('Technical Submittals'),
            'type': 'ir.actions.act_window',
            'res_model': 'construction.submittal',
            'view_mode': 'kanban,tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id}
        }
