# -*- coding: utf-8 -*-
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    peppol_server_id = fields.Many2one("peppol.server", string="Peppol Server")
