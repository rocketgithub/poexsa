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


class PoexsaIngresoProducto(models.Model):
    _name = 'poexsa.ingreso_producto'

    def _default_pos(self):
        default_pos_id = False
        if self.env.user.default_pos_id:
            default_pos_id = self.env.user.default_pos_id.id
        return default_pos_id

    producto_id = fields.Many2one('product.template','Producto')
    fecha = fields.Date('Fecha')
    cantidad = fields.Float('Cantidad')
    default_pos_id = fields.Many2one("pos.config", string="Punto de Venta por Defecto", efault=_default_pos,)

class PoexsaGrupoCuadre(models.Model):
    _name = 'poexsa.grupo_cuadre'

    name = fields.Char('Nombre')
