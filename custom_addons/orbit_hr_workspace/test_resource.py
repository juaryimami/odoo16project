import odoo
from odoo import api, SUPERUSER_ID
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'construction_db'])
registry = odoo.registry('construction_db')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    cal = env['resource.calendar']
    print(dir(cal))
