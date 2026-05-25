from odoo import models, fields,api

class EdomiasLocation(models.Model):
    _name = 'agent.location'
    _description = 'Edomias Location'

    name = fields.Char(string='Location Name', required=True)
    description = fields.Text(string='Location Description')
    create_date = fields.Datetime(string="Created Date", readonly=True, default=fields.Datetime.now)
    # Add other common fields for location

    # Foreign key to TaxRegion
    income_tax_region_id = fields.Many2one('tax.region', string='Income Tax Region')
    tension_tax_region_id = fields.Many2one('tax.region', string='Pension Tax Region')
    is_desert = fields.Boolean(string='Is Desert Area')

    @api.onchange('income_tax_region_id')
    def _onchange_income_tax_region(self):
        if self.income_tax_region_id:
            # Set tension tax region to the same value by default
            if not self.tension_tax_region_id:
                self.tension_tax_region_id = self.income_tax_region_id


