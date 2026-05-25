{
    'name': 'Performance Edomias',
    'version': '17.0',
    'summary': 'Performance Edomias',
    'description': """Performance Edomias""",
    'category': 'Human Resource',
    'website': '',
    'depends': [
        'base',
        'base_setup',
        'hr',
        'hr_contract'],

    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'views/employee_appraisal.xml',
        'views/employee_kpi.xml',
        # 'views/performance_line.xml',
        'views/probation_contract_date.xml',
        # 'views/probation_evaluation.xml'

    ],
    'assets': {},
    'installable': True,
    'application': True,
}
