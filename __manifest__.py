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

    'depends': ['base','point_of_sale','fel_infile','pos_gt'],

    'data': [
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
