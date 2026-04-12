# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectPhaseConfig(models.Model):
    _name = 'project.phase.config'
    _description = 'Specific Phase Weights Per Project'
    _order = 'sequence, id'

    project_id = fields.Many2one('project.project', string='Project', required=True, ondelete='cascade')
    phase_id = fields.Many2one('construction.phase', string='Construction Phase', required=True)
    sequence = fields.Integer(string='Sequence', related='phase_id.sequence', store=True)
    weight = fields.Float(string='Assigned Weight (%)', default=0.0)
    
    # Computed Progress Data
    total_jobs = fields.Integer(string='Total Jobs in Phase', compute='_compute_phase_stats')
    completed_jobs = fields.Integer(string='Jobs Passed / Completed', compute='_compute_phase_stats')
    phase_progress_ratio = fields.Float(string='Phase Completion (%)', compute='_compute_phase_stats')
    contribution = fields.Float(string='Project Progress Contribution (%)', compute='_compute_phase_stats')

    @api.depends('project_id.job_order_ids', 'project_id.job_order_ids.progress_ratio', 'weight')
    def _compute_phase_stats(self):
        for config in self:
            # 1. Find jobs for this project in this configuration's phase
            jobs = config.project_id.job_order_ids.filtered(lambda j: j.phase_id.id == config.phase_id.id)
            total = len(jobs)
            
            # 2. Sum granular progress ratios
            agg_progress = sum(jobs.mapped('progress_ratio'))
            
            config.total_jobs = total
            config.completed_jobs = len(jobs.filtered(lambda j: j.is_inspected_passed))
            
            if total > 0:
                # Granular Phase Progress is the average of its jobs
                ratio = agg_progress / total
                config.phase_progress_ratio = ratio
                config.contribution = (config.weight * ratio) / 100.0
            else:
                config.phase_progress_ratio = 0.0
                config.contribution = 0.0
