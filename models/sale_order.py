# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    franquicia_po = fields.Char("Franquicia PO", readonly=True)
    franquicia = fields.Char('Franquicia' , readonly=True)
