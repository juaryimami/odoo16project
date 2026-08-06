# pyrefly: ignore [missing-import]
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Check if this allocation is for Compensation Leave and has a date_from
            if vals.get('holiday_status_id') and vals.get('date_from'):
                leave_type = self.env['hr.leave.type'].browse(vals['holiday_status_id'])
                if leave_type.is_comp_leave:
                    date_from = fields.Date.to_date(vals['date_from'])
                    # Enforce strictly 1 month validity
                    vals['date_to'] = date_from + relativedelta(months=1)
        return super(HrLeaveAllocation, self).create(vals_list)

    def write(self, vals):
        # Prevent manual changes to date_to for comp leave, or ensure it stays 1 month if date_from changes
        res = super(HrLeaveAllocation, self).write(vals)
        if 'date_from' in vals or 'holiday_status_id' in vals:
            for alloc in self:
                if alloc.holiday_status_id.is_comp_leave and alloc.date_from:
                    new_date_to = alloc.date_from + relativedelta(months=1)
                    if alloc.date_to != new_date_to:
                        alloc.date_to = new_date_to
        return res

    @api.model
    def _action_expire_orbit_allocations(self):
        """
        Cron job method to find and expire annual leave allocations 
        that are older than 2 years.
        """
        # Find all validated allocations older than 2 years
        two_years_ago = fields.Date.today() - relativedelta(years=2)
        
        # Usually Annual Leave requires allocation. Let's find allocations 
        # that don't already have an expiration date (or their expiration is past)
        # We assume Annual Leave type has requires_allocation == 'yes'
        # To be completely safe, we can add a boolean on leave type 'expires_in_2_years'
        # but the SRS states Annual Leave must be used within 2 years.
        
        # Searching for allocations created 2+ years ago that still have a balance
        allocations = self.search([
            ('state', '=', 'validate'),
            ('date_from', '<=', two_years_ago),
            ('holiday_status_id.requires_allocation', '=', 'yes'),
        ])

        expired_count = 0
        for alloc in allocations:
            # We must check if there is any remaining leave balance for this specific allocation
            # Odoo 16 hr.leave.allocation has 'leaves_taken' and 'number_of_days'
            remaining = alloc.number_of_days - alloc.leaves_taken
            
            if remaining > 0:
                # Create a negative allocation to zero out this balance
                # Or use Odoo 16 native allocation validity dates if applicable.
                # Setting date_to on the original allocation might be cleaner if it's supported.
                
                # In Odoo 16, setting the validity date (date_to) prevents usage after that date.
                # However, it doesn't cleanly zero the balance in all reports unless we deduct it.
                # To deduct, we can just create a negative allocation or update date_to.
                
                try:
                    # Best native approach in Odoo 16: set date_to to yesterday so it's expired.
                    alloc.write({'date_to': fields.Date.today() - relativedelta(days=1)})
                    expired_count += 1
                except Exception as e:
                    _logger.error(f"Failed to expire allocation {alloc.id}: {e}")
                    
        _logger.info(f"Orbit Leave Cron: Expired {expired_count} old annual leave allocations.")
