# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import hashlib
import json

import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from requests.auth import HTTPBasicAuth

TEMPORARY_NETWORK_ERROR_CODES = {502, 503}


class PeppolTemporaryNetworkError(Exception):
    pass


class PeppolServer(models.Model):
    _name = "peppol.server"
    _description = "Peppol Server"

    name = fields.Char(default="Edido")
    url = fields.Char(default="https://api.edido.eu/peppol/send_ubl", required=True)
    url_feedback = fields.Char(default="https://api.edido.eu/peppol/get_sending_status")
    account_user = fields.Char(string="User", copy=False)
    account_password = fields.Char(string="Password", copy=False)

    history_ids = fields.One2many(
        "peppol.history",
        "server_id",
        string="History",
        readonly=True,
    )

    def _auth(self):
        self.ensure_one()
        return HTTPBasicAuth(self.account_user or "", self.account_password or "")

    def _log(self, record, document):
        self.ensure_one()
        md5 = hashlib.md5(document).hexdigest()
        self.env["peppol.history"].sudo().create(
            {
                "server_id": self.id,
                "document": "%s,%s" % (record._name, record.id),
                "md5": md5,
                "is_sending": True,
            }
        )

    def _send_ubl(self, record, ubl):
        self.ensure_one()
        file_data = {"file": ubl}
        response = requests.post(self.url.lower(), auth=self._auth(), files=file_data)
        if response.status_code in TEMPORARY_NETWORK_ERROR_CODES:
            raise PeppolTemporaryNetworkError(
                _(
                    "HTTP error {} sending UBL: {}".format(
                        response.status_code, response.text
                    )
                )
            )
        if response.status_code != 200:
            raise UserError(
                _(
                    "HTTP error {} sending UBL: {}".format(
                        response.status_code, response.text
                    )
                )
            )
        self._log(record, ubl)
        return response

    def _cron_check_status(self):
        servers = self.search([])
        servers.sudo().check_status()

    def check_status(self):
        for server in self:
            if not server.url_feedback:
                continue
            sending = server.history_ids.search([("is_sending", "=", True)])
            if not sending:
                continue
            data = {"md5": [s.md5 for s in sending]}
            response = requests.post(
                server.url_feedback.lower(), auth=server._auth(), json=data
            )
            if response.status_code != 200:
                raise UserError(
                    _(
                        "HTTP error {} collecting UBL feedback: {}".format(
                            response.status_code, response.text
                        )
                    )
                )
            status = json.loads(response.text).get("status", {})
            for msg in sending:
                msg.is_sending = not status.get(msg["md5"], True)
                if status.get(msg["md5"]) and msg.document:
                    msg.document._peppol_export_confirmed()

    def button_peppol_history(self):
        action = self.env.ref("account_invoice_export_ubl.peppol_history_action").read()[0]
        if self.env.context.get("active_model") == "peppol_server":
            action["domain"] = [("server_id", "=", self.env.context.get("active_id"))]
        return action


class PeppolHistory(models.Model):
    _name = "peppol.history"
    _description = "Peppol Exchanges History"
    _order = "id desc"

    server_id = fields.Many2one(
        "peppol.server",
        required=True,
    )
    document = fields.Reference(
        selection="_get_document_models",
        readonly=True,
    )
    md5 = fields.Char(
        readonly=True,
    )
    is_sending = fields.Boolean(
        index=True, help="The document is being transported to the other party"
    )

    @api.model
    def _get_document_models(self):
        models = [self.env["account.move"]]
        return [(model._name, model._description) for model in models]
