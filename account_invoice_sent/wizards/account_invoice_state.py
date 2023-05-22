# -*- coding: utf-8 -*-
# Copyright 2015-2018 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class AccountInvoiceSent(models.TransientModel):
    """
    This wizard will mark as sent the all the selected validated invoices
    """

    _name = "account.invoice.sent"

    count_print = fields.Integer("To print", readonly=True)
    count_email = fields.Integer("By email", readonly=True)
    count_email_missing = fields.Integer("Email address missing", readonly=True)

    email_copy = fields.Boolean(
        "Send copy by email", help="For printed documents", default=False
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super(AccountInvoiceSent, self).default_get(fields_list)
        active_ids = self._context.get("active_ids", [])
        if active_ids is None:
            return {}
        invoices = self.env["account.invoice"].browse(active_ids)
        invoices = invoices._filter_send_invoice()
        defaults["count_print"] = len(invoices._filter_send_invoice("letter"))
        invoices_email = invoices.filtered(
            lambda r: r.partner_id.commercial_partner_id.invoice_sending_method
            == "email"
        )
        defaults["count_email"] = len(invoices_email)
        defaults["count_email_missing"] = len(invoices_email) - len(
            invoices_email.filtered("partner_id.commercial_partner_id.email")
        )
        return defaults

    @api.multi
    def button_print(self):
        # TODO create a model to show the attachments and
        # create jobs on them
        act_close = {"type": "ir.actions.act_window_close"}
        active_ids = self._context.get("active_ids", [])
        if active_ids is None:
            return act_close
        invoices = self.env["account.invoice"].browse(active_ids)
        invoices = invoices._filter_send_invoice("letter")
        invoice_print = self.env["account.invoice.print"].create(
            {"invoice_ids": [(6, 0, invoices.ids)], "send_email_copy": self.email_copy}
        )
        invoice_print.with_delay(priority=20).generate_report()
        self.env.user.notify_info(_("A report will be generated in the background."))
        return {"type": "ir.actions.act_window_close"}

    def _send_action(self, sending_method):
        active_ids = self._context.get("active_ids", [])
        if not active_ids:
            return
        invoices = self.env["account.invoice"].browse(active_ids)
        invoices = invoices._filter_send_invoice(sending_method)
        invoices.with_delay(priority=50)._generate_send_invoice(sending_method)

    @api.multi
    def button_email(self):
        self._send_action("email")
        self.env.user.notify_info(_("Invoices will be sent by email in the background."))
        return {"type": "ir.actions.act_window_close"}

    @api.multi
    def button_mark_only(self):
        act_close = {"type": "ir.actions.act_window_close"}
        active_ids = self._context.get("active_ids", [])
        if active_ids is None:
            return act_close
        invoices = self.env["account.invoice"].browse(active_ids)
        invoices = invoices._filter_send_invoice()
        invoices.write({"sent": True})
        for invoice in invoices:
            invoice.message_post(body=_("Invoice sent"))
        return act_close
