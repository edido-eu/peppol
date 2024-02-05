# Copyright 2020 Camptocamp SA
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import odoo
from lxml import etree
from odoo import _, fields, models
from odoo.exceptions import UserError, except_orm


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_exported = fields.Boolean(copy=False)
    invoice_export_confirmed = fields.Boolean(copy=False)

    def peppol_export_invoice(self):
        """Export ebill to external server and update the chatter."""
        invoices_in_error = self.browse()
        for invoice in self:
            if not invoice.is_invoice():
                continue
            if invoice.invoice_exported:
                continue
            try:
                invoice._peppol_export_invoice()
                invoice._peppol_sending_log_success()
            except Exception as e:
                invoices_in_error |= invoice
                values = {
                    "error_detail": "",
                    "error_type": type(e).__name__,
                }
                if isinstance(e, except_orm):
                    values["error_detail"] = e.name
                elif hasattr(e, "message"):
                    values["error_detail"] = e.message
                else:
                    values["error_detail"] = str(e)
                with odoo.api.Environment.manage():
                    with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                        # Create a new environment with new cursor database
                        new_env = odoo.api.Environment(
                            new_cr, self.env.uid, self.env.context
                        )
                        # The chatter of the invoice need to be updated, when the job fails
                        invoice.with_env(new_env)._peppol_sending_log_error(values)
        if invoices_in_error == self:
            raise UserError("Peppol sending failed")

    def _peppol_export_invoice(self):
        """Export electronic invoice to external service."""
        self.ensure_one()
        ubl = self.generate_ubl_xml_string()
        server = self.env.user.company_id.peppol_server_id.sudo()
        if not server:
            raise UserError("Please define peppol server in the Accounting Settings")
        res = server._send_ubl(self, ubl)
        self.write({
            "invoice_exported": True,
            "is_move_sent": True,
        })
        return res.text

    def _peppol_export_confirmed(self):
        """Confirm successful sending of electronic invoice."""
        self.ensure_one()
        self.invoice_export_confirmed = True

    def _peppol_sending_log_error(self, values):
        template = "account_invoice_export_ubl.sending_invoice_exception"
        message = self.env["ir.ui.view"]._render_template(template, values=values)
        self.message_post(body=message)

    def _peppol_sending_log_success(self):
        self.message_post(body=_("Invoice successfuly sent in UBL"))
