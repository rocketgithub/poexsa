# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    grupo_cuadre_id = fields.Many2one('poexsa.grupo_cuadre', 'Grupo de cuadre')
