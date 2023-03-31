# -*- coding: utf-8 -*-
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from requests.auth import HTTPBasicAuth

from odoo import models, fields


class PeppolServer(models.Model):
    _name = "peppol.server"

    name = fields.Char()
    url = fields.Char()
    user = fields.Char(copy=False)
    password = fields.Char(copy=False)

    def _auth(self):
        self.ensure_one()
        return HTTPBasicAuth(self.user or "", self.password or "")
