# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
import os
import tempfile
from contextlib import closing

from odoo import _, api, fields, models

from odoo.addons.queue_job.job import job


class AccountInvoicePrint(models.Model):
    _name = "account.invoice.print"

    invoice_ids = fields.Many2many(comodel_name="account.invoice", readonly=True)
    send_email_copy = fields.Boolean(readonly=True)
    document = fields.Binary(
        comodel_name="ir.attachment", attachment=True, readonly=True
    )
    fname = fields.Char(compute="_compute_file_name")
    state = fields.Selection(
        selection=[("progress", "In Progress"), ("done", "Done")],
        required=True,
        readonly=True,
        default="progress",
    )

    def _compute_file_name(self):
        for record in self:
            record.fname = u"account_invoice_print_{}.pdf".format(self.id)

    @api.model
    def _save_document_content(self, content, invoice):
        # for test purpose, set the invoice id as prefix
        pdfreport_fd, pdfreport_path = tempfile.mkstemp(
            suffix=".pdf", prefix="invoice.%s." % invoice.id
        )
        with closing(os.fdopen(pdfreport_fd, "w")) as pdfreport:
            pdfreport.write(content)
        return pdfreport_path

    @api.model
    def _get_existing_documents(self, invoices):
        """
            @return: dictionary of document path by invoice
        """
        attachment = self.env["report"]._check_attachment_use(
            invoices.ids,
            self.env["report"]._get_report_from_name("account.report_invoice"),
        )
        loaded_documents = attachment["loaded_documents"]
        ret = {}
        for invoice in invoices:
            document = loaded_documents.get(invoice.id)
            if not document:
                continue
            ret[invoice] = self._save_document_content(document, invoice)
        return ret

    @api.model
    def _generate_missing_documents(self, invoices, existing_document_by_invoice):
        """
            Generate the missing invoices
            The generation is done by partner
            @return: dictionary of document path by invoice
        """
        expected_invoice_ids = set(invoices.ids)
        found_invoice_ids = {i.id for i in existing_document_by_invoice.keys()}
        missing_invoice_ids = expected_invoice_ids - found_invoice_ids
        ret = {}
        for invoice_id in missing_invoice_ids:
            missing_invoice = self.env["account.invoice"].browse(invoice_id)
            document = self.env["report"].get_pdf(
                missing_invoice.ids, "account.report_invoice"
            )
            ret[missing_invoice] = self._save_document_content(
                document, missing_invoice
            )
        return ret

    @classmethod
    def _cleanup_temporary_files(cls, temporary_files):
        # Manual cleanup of the temporary files
        for path in temporary_files:
            try:
                os.unlink(path)
            except (OSError, IOError):
                logging.getLogger(__name__).error(
                    "Error when trying to remove file %s", path
                )

    @api.model
    def _merge_documents(self, pdfdocuments):
        if len(pdfdocuments) == 1:
            return pdfdocuments[0]
        return self.env["report"]._merge_pdf(pdfdocuments)

    @api.multi
    def _notify_report_generated(self):
        self.ensure_one()
        action_xmlid = "account_invoice_sent.action_account_invoice_print_form"
        action = self.env.ref(action_xmlid).read()[0]
        action.update({"res_id": self.id, "views": [(False, "form")]})
        self.env.user.notify_info(
            _("A report for invoices is available."), sticky=True, action=action
        )

    @job(default_channel="root.background.invoice_print")  # priority=20
    def generate_report(self):
        """Generate a pdf report for all invoices"""
        self.ensure_one()
        # we need to apply the filter because the state may have
        # changed since when we delayed the job
        invoices = self.invoice_ids._filter_send_invoice(sending_method="letter")

        self.state = "done"

        if not invoices:
            return None

        template = self.env.ref("account.email_template_edi_invoice")
        for invoice in invoices:
            invoice.message_post(body=_("Invoice sent"))
            if self.send_email_copy:
                template.send_mail(invoice.id)

        # In Odoo 13 we should only call and return the result of
        # self.env['report'].get_pdf(
        # Unfortunately un Odoo 10, the basic implementation generates the pdf
        # of all the reports even if an attachment already exists.
        # (even if the existing attachment is the one used into the final result)
        # To avoid this performance cost, we re implement the logic of checking
        # existing reports and only generates the missing one before merging all
        # the reports into a single file
        # TO BE REMOVED into Odoo 13
        document_by_invoice = self._get_existing_documents(invoices)
        document_by_invoice.update(
            self._generate_missing_documents(invoices, document_by_invoice)
        )

        # sort all the invoices by partner ref and num
        sorted_invoices = invoices.sorted(
            lambda i: (i.partner_id.name and i.partner_id.name.lower(), i.number)
        )

        # sort path to generate a single document where invoices are ordered by
        # partner.ref, invoice.number
        pdfdocuments = []
        for invoice in sorted_invoices:
            path = document_by_invoice.get(invoice)
            if not path:
                return None
            pdfdocuments.append(path)

        temporary_files = set(pdfdocuments)

        # get final result and save-it
        entire_report_path = self._merge_documents(pdfdocuments)
        temporary_files.add(entire_report_path)
        with open(entire_report_path, "rb") as pdfdocument:
            content = pdfdocument.read()
        self.document = base64.b64encode(content)
        invoices.write({"sent": True})

        self._notify_report_generated()

        # Manual cleanup of the temporary files
        self._cleanup_temporary_files(temporary_files)

        # return the ordered list of generated files for test purpose only....
        return pdfdocuments

    def action_view_invoice(self):
        invoices = self.mapped("invoice_ids")
        action = self.env.ref("account.action_invoice_tree1").read()[0]
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            action["views"] = [(self.env.ref("account.invoice_form").id, "form")]
            action["res_id"] = invoices.ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action
