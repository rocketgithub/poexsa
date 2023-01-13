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

    def obtener_cliente_nit_sat(self,data):
        partner_id = False
        headers = { "Content-Type": "application/json" }
        company_id = self.env['res.company'].search([('id','=',data[1])])
        if company_id:
            data = {
                "emisor_codigo": company_id.usuario_fel,
                "emisor_clave": company_id.clave_fel,
                "nit_consulta": nit[0].replace('-',''),
            }
            r = requests.post('https://consultareceptores.feel.com.gt/rest/action', json=data, headers=headers)
            logging.warning(r.text)
            if r and r.json():
                datos_nit = r.json()
                partner_dic = {
                    'name': datos_nit['nombre'],
                    'vat': data[0],
                }
                partner_id = self.env['res.partner'].create(partner_dic)
            else:
                raise UserError(_("Error en respuestas"))
        return partner_id
