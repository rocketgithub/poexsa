# -*- coding: utf-8 -*-
{
    'name': "POEXSA",

    'summary': """ Módulo para Poexsa """,

    'description': """
        Módulo para Poexsa
    """,

    'author': "Aquih",
    'website': "http://www.aquih.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','point_of_sale','pos_gt','product'],

    'data': [
        'views/poexa_views.xml',
        'views/product_template_views.xml',
        'views/product_views.xml',
        'views/pos_config_views.xml',
        'wizard/poexsa_reporte_cuadre_ventas_wizard.xml',
        'views/reporte_payment1.xml',
        'views/reporte_payment2.xml',
        'views/reporte_payment3.xml',
        'views/reporte_payment4.xml',
        'views/reporte_payment5.xml',
        'views/reporte_payment6.xml',
        'views/reports.xml',
        'views/report_views.xml',
        'security/ir.model.access.csv',
    ],
    'assets':{
        'point_of_sale.assets': [
            'poexsa/static/src/js/**/*.js',
        ],
        'web.assets_qweb':[
            'poexsa/static/src/xml/**/*.xml',
        ],
        'web.assets_backend': [
        ],
    },
    'license': 'LGPL-3',
}
