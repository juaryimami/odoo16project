{
    'name': 'Book Club Management',
    'version': '1.0',
    'category': 'Sales/Book Club',
    'summary': 'Manage authors, publishers, books, members and borrowing workflow',
    'description': """
        Book Club Application
        =====================
        Features:
        - Authors Management
        - Publisher Management
        - Genres Configuration
        - Books Management
        - Members Management
        - Borrow Workflow
        - Reports & Dashboards
    """,
    'author': 'Your Company',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/author_views.xml',
        'views/publisher_views.xml',
        'views/genre_views.xml',
        'views/book_views.xml',
        'views/member_views.xml',
        'views/borrow_views.xml',
        'views/report_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
