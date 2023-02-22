# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import collections
import re

import requests
import logging
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'

    def obtener_cliente_nit_sat(self, data_cliente):
        query = data_cliente[0]
        fields = data_cliente[1]
        company_id = data_cliente[2]

        company_id = self.env['res.company'].search([('id','=',company_id)])

        if company_id:
            data = {
                "emisor_codigo": company_id.usuario_fel,
                "emisor_clave": company_id.clave_fel,
                "nit_consulta": query.replace('-',''),
            }
            headers = { "Content-Type": "application/json" }
            r = requests.post('https://consultareceptores.feel.com.gt/rest/action', json=data, headers=headers)
            logging.warning(r.text)
            
            if r and r.json() and r.json()['nombre']:
                datos_nit = r.json()
            
                partner_dic = {
                    'name': datos_nit['nombre'],
                    'vat': datos_nit['nit'],
                }
                partner = self.create(partner_dic)
                return partner.read(fields)
        return []
