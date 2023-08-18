# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import collections
import re

import requests
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

    def _default_products(self):
        lineas = []
        producto_ids = self.env['product.template'].search([('grupo_cuadre_id','!=',False)])
        for producto in producto_ids:
            linea = {'producto_id': producto.id, 'cantidad': 0}
            lineas.append((0,0,linea))
        return lineas

    producto_id = fields.Many2one('product.template','Producto')
    ingreso_producto_linea_ids = fields.One2many('poexsa.ingreso_producto_linea','ingreso_id', 'Ingreso grupo de cuadres', default= _default_products)
    fecha = fields.Date('Fecha')
    cantidad = fields.Float('Cantidad')
    default_pos_id = fields.Many2one("pos.config", string="Punto de Venta por Defecto", default=_default_pos)

class PoexsaGrupoCuadre(models.Model):
    _name = 'poexsa.grupo_cuadre'

    name = fields.Char('Nombre')
    producto_ids = fields.One2many('product.template','grupo_cuadre_id','Productos')

class PoexsaIngresoProductoLinea(models.Model):
    _name = 'poexsa.ingreso_producto_linea'

    ingreso_id = fields.Many2one('poexsa.ingreso_producto','Ingreso producto')
    producto_id = fields.Many2one('product.template','Productos')
    cantidad = fields.Float('Cantidad')
    sobrante = fields.Float('Sobrante')
