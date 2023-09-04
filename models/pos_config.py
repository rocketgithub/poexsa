# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    monitor = fields.Boolean("Monitor")
