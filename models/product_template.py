# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    grupo_cuadre_id = fields.Many2one('poexsa.grupo_cuadre', 'Grupo de cuadre')
    reporte_ventas_franquicia = fields.Boolean('Reporte de ventas por franquicia')
