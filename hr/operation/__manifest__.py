{
    'name': 'Opration Module',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Custom Opration',
    'depends': ['base','hr_contract','hr','purchase','sale','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/location_views.xml',
        'views/edomias_views.xml',
        'data/email_templates.xml',  # Include the email templates
        'data/piece_rate_salary_rule.xml',
        'views/agent_project_renewal_views.xml',
        'views/project_views.xml',
        'data/cron_jobs.xml',
        'views/assets.xml',
        'views/hr_contract_views.xml',
        'views/purchase_order_views.xml',
        'views/custom_sales_order.xml',
        'views/tax_region_view.xml',
        'views/operation_desert_allowance.xml',
        'views/piece_rate_activity_view.xml',
        'views/piece_rate_uom_view.xml',
        'views/ot_rate_list_view.xml',
        'views/employee_activity_view.xml',
        'views/opretion_resource_form_view.xml',
        'reports/inherit_sales_invoice_template.xml',
        'views/custom_product_view.xml',
        'views/menu_views.xml',
    ],

'assets': {
        'web.assets_frontend': [
            'operation/static/src/css/custom_styles.css',
        ],
    'web.assets_backend': [
        'operation/static/src/css/custom_styles.css'
        'operation/static/src/js/project_date_restriction.js',


    ],
    },
    'installable': True,
    'application': True,
   'images': 'static/description/icon.png',
}
