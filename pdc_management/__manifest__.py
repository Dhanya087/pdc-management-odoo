{
    'name': 'Cheque Management (PDC)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Finance',
    'summary': 'Manage and track post-dated cheques',
    'description': """
Cheque Management (PDC)
======================

Features:
- Bank Details Management
- Cheque Entry and Tracking
- Payee Management
- Automatic Cheque Status Classification
- Automated Alerts and Reminders
- Filters and Reports
    """,
    'author': 'Dhanya',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
    ],
    'data': [
        'security/pdc_security.xml',
        'security/ir.model.access.csv',
        'data/pdc_sequence.xml',
        'data/pdc_cron.xml',
        'views/pdc_bank_views.xml',
        'views/pdc_payee_views.xml',
        'views/pdc_cheque_views.xml',
        'views/pdc_dashboard_views.xml',
        'views/pdc_menu.xml',
        'views/pdc_fail_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pdc_management/static/src/css/pdc_dashboard.css',
            'pdc_management/static/src/js/pdc_dashboard.js',
            'pdc_management/static/src/xml/pdc_dashboard_template.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}