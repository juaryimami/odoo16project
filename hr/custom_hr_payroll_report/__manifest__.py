{
    'name': 'Custom Payroll Report',
    'version': '1.0',
    'summary': 'Custom Payroll Report',
    'sequence': 100,
    'description': """
        Custom Payroll Report module.
    """,

    'depends': ['base','om_hr_payroll','hr_holidays'],
     'data': [
         'security/ir.model.access.csv',
         'views/menu.xml',
         'views/custom_hr_payroll_report_view.xml',
         'views/request_payroll_report_form_view.xml',
          "reports/print_hr_employee_payroll_bank_latter.xml",
         'wizards/report_wizard_view.xml',
     ],
    'assets': {
    },
    'installable': True,
    'auto_install': False,
}
           

        
