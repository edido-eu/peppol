# -*- coding: utf-8 -*-
# Copyright 2015-2018 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models

from odoo.addons.queue_job.job import job, related_action


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # Allow to change value in 'open' state
    sent = fields.Boolean(readonly=True, states={"open": [("readonly", False)]})

    sending_method = fields.Selection(
        readonly=True,
        related="commercial_partner_id.invoice_sending_method",
        string="Sending Method",
    )

    @api.multi
    def _filter_send_invoice(self, sending_method=None):
        def f_state(r):
            return not r.sent and r.state not in ("draft", "proforma", "proforma2")

        def f_sending_method(r):
            return r.sending_method == sending_method

        def f_email(r):
            return bool(r.partner_id.email)

        filters = [f_state]
        if sending_method:
            filters.append(f_sending_method)
        if sending_method == "email":
            filters.append(f_email)

        return self.filtered(lambda r: all(f(r) for f in filters))

    @job(default_channel="root.background.invoice_send")  # priority=50
    @related_action(action="related_action_open_invoice")
    def _generate_send_invoice(self, sending_method):
        """Generate jobs to send invoices"""
        invoices = self.exists()
        invoices = invoices._filter_send_invoice(sending_method)
        method_name = u"_send_invoice_{}".format(sending_method)
        for invoice in invoices:
            getattr(invoice.with_delay(priority=50), method_name)()

    @job(default_channel="root.background.invoice_send")  # priority=50
    @related_action(action="related_action_open_invoice")
    def _send_invoice_email(self):
        """Generate and send an invoice by email"""
        # we need to apply the filter because the state may have
        # changed since when we delayed the job
        invoices = self.exists()._filter_send_invoice(sending_method="email")
        if not invoices:
            return
        invoices.write({"sent": True})
        template = self.env.ref("account.email_template_edi_invoice")
        for invoice in invoices:
            invoice.message_post(body=_("Invoice sent"))
            template.send_mail(invoice.id)
