# -*- coding: utf-8 -*-

from odoo import models, fields, api


class res_company(models.Model):
    _inherit = 'res.company'

    empresa_compra_id = fields.Many2one('poexsa.franquicia')
