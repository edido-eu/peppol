# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tests import SavepointCase


class TestAccountInvoicePring(SavepointCase):
    @classmethod
    def setUpClass(cls):
        """
        Create 3 partners with 2 invoices by partner
        Only partner 0 and 2 should received invoice by letter
        """
        super(TestAccountInvoicePring, cls).setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
            )
        )

        cls.AccountAccount = cls.env["account.account"]
        cls.AccountInvoice = cls.env["account.invoice"]
        cls.AccountInvoiceLine = cls.env["account.invoice.line"]
        cls.AccountInvoicePrint = cls.env["account.invoice.print"]
        cls.AccountJournal = cls.env["account.journal"]

        # INSTANCES

        # Instance partner
        # only partner 0 and 2 should received invoice by letter
        for i in range(3):
            partner = cls.env["res.partner"].create(
                {
                    "name": u"TEST %s" % i,
                    "ref": "%s" % i,
                    "invoice_sending_method": "letter" if not i % 2 else "email",
                }
            )
            setattr(cls, "partner_%s" % i, partner)

        # Instance: company
        cls.company = cls.env.ref("base.main_company")

        # Instance: account type (receivable)
        cls.type_recv = cls.env.ref("account.data_account_type_receivable")

        # Instance: account type (payable)
        cls.type_payable = cls.env.ref("account.data_account_type_payable")

        # Instance: account (receivable)
        cls.account_recv = cls.AccountAccount.create(
            {
                "name": "test_account_receivable",
                "code": "123",
                "user_type_id": cls.type_recv.id,
                "company_id": cls.company.id,
                "reconcile": True,
            }
        )

        # Instance: account (payable)
        cls.account_payable = cls.AccountAccount.create(
            {
                "name": "test_account_payable",
                "code": "321",
                "user_type_id": cls.type_payable.id,
                "company_id": cls.company.id,
                "reconcile": True,
            }
        )

        # Instance: partner
        cls.partner = cls.env.ref("base.res_partner_2")

        # Instance: journal
        cls.journal = cls.AccountJournal.search([("code", "=", "BILL")])

        # Instance: product
        cls.product = cls.env.ref("product.product_product_4")

        cls.invoices = cls.AccountInvoice.browse()
        # create 2 invoices for each partner
        for i in range(2):
            for p in range(3):
                partner = getattr(cls, "partner_%s" % p)
                # Instance: invoice line
                cls.invoice_line = cls.AccountInvoiceLine.create(
                    {
                        "name": u"test {} {}".format(i, p),
                        "account_id": cls.account_payable.id,
                        "price_unit": 100.00 * p * i,
                        "quantity": 1,
                        "product_id": cls.product.id,
                    }
                )

                # Instance: invoice
                invoice = cls.AccountInvoice.create(
                    {
                        "partner_id": partner.id,
                        "account_id": cls.account_recv.id,
                        "journal_id": cls.journal.id,
                        "invoice_line_ids": [(4, cls.invoice_line.id)],
                    }
                )
                setattr(cls, u"partner_{}_invoice_{}".format(p, i), invoice)
                cls.invoices |= invoice
        cls.invoices.action_invoice_open()

    def setUp(self):
        super(TestAccountInvoicePring, self).setUp()
        # mute logger
        loggers = ["odoo.addons.queue_job.models.base"]
        for logger in loggers:
            logging.getLogger(logger).addFilter(self)

        # pylint: disable=unused-variable
        @self.addCleanup
        def un_mute_logger():
            for logger_ in loggers:
                logging.getLogger(logger_).removeFilter(self)

    def filter(self, record):
        # required to mute logger
        return 0

    def _print_invoices(self, invoices):
        invoice_print = self.AccountInvoicePrint.create(
            {"invoice_ids": [(6, 0, invoices.ids)]}
        )
        return invoice_print.generate_report()

    def _sort_invoices(self, invoices):
        return invoices.sorted(
            lambda i: (i.partner_id.name and i.partner_id.name.lower(), i.number)
        )

    def _get_invoice_ids_from_invoices_path(self, invoices_path):
        return [int(p.split(".")[1]) for p in invoices_path]

    def _generate_invoice_document(self, invoice):
        self.env["report"].get_pdf(invoice.ids, "account.report_invoice")

    def assertAttachementCount(self, instances, count):
        attachement_count = self.env["ir.attachment"].search_count(
            [("res_id", "in", instances.ids), ("res_model", "=", instances._name)]
        )
        self.assertEqual(count, attachement_count)

    def test_00(self):
        """
        Data:
            partner_0 with 2 invoices and invoice_sending_method "letter"
            partner_1 with 2 invoice and invoice_sending_method "email"
            partner_2 with 2 invoice and invoice_sending_method "letter"
        Test case:
            Print all the invoices with the wizard
        Expected result:
            * 4 invoices are printed (partner_0 and partner_2) for sending
            method "letter"
            * invoices are sorted by partner's ref and invoice number
        """
        invoices_path = self._print_invoices(self.invoices)
        self.assertTrue(invoices_path)
        self.assertEqual(4, len(invoices_path))
        sorted_invoices = self._sort_invoices(
            self.invoices.filtered(
                lambda a: a.partner_id in (self.partner_0, self.partner_2)
            )
        )
        self.assertListEqual(
            sorted_invoices.ids, self._get_invoice_ids_from_invoices_path(invoices_path)
        )
        self.assertAttachementCount(self.invoices, 4)

    def test_01(self):
        """
        Data:
            partner_0 with 2 invoices and invoice_sending_method "letter"
            partner_1 with 2 invoice and invoice_sending_method "email"
            partner_2 with 2 invoice and invoice_sending_method "letter"
        Test case:
            Generate 1 invoice for partner_0 and 1 for parnter_2 before using the
            wizard (the attachment will therefore already exists when the wizard
            will be called)
            Print all the invoices with the wizard
        Expected result:
            * 4 invoices are printed (partner_0 and partner_2) for sending
            method "letter"
            * invoices are sorted by partner's ref and invoice number
        """
        self.assertAttachementCount(self.invoices, 0)
        self._generate_invoice_document(self.partner_0_invoice_0)
        self._generate_invoice_document(self.partner_2_invoice_1)
        self.assertAttachementCount(self.invoices, 2)
        invoices_path = self._print_invoices(self.invoices)
        self.assertTrue(invoices_path)
        self.assertEqual(4, len(invoices_path))
        sorted_invoices = self._sort_invoices(
            self.invoices.filtered(
                lambda a: a.partner_id in (self.partner_0, self.partner_2)
            )
        )
        self.assertListEqual(
            sorted_invoices.ids, self._get_invoice_ids_from_invoices_path(invoices_path)
        )
        self.assertAttachementCount(self.invoices, 4)

    def test_02(self):
        """
        Data:
            partner_0 with 2 invoices and invoice_sending_method "letter"
            partner_1 with 2 invoice and invoice_sending_method "email"
            partner_2 with 2 invoice and invoice_sending_method "letter"
        Test case:
            Change invoice_sending_method to "letter"
            Print all the invoices with the wizard
        Expected result:
            * 6 invoices are printed (partner_0, partner_1 and partner_2)
            * invoices are sorted by partner's ref and invoice number
        """
        self.assertAttachementCount(self.invoices, 0)
        self.partner_1.invoice_sending_method = "letter"
        invoices_path = self._print_invoices(self.invoices)
        self.assertTrue(invoices_path)
        self.assertEqual(6, len(invoices_path))
        sorted_invoices = self._sort_invoices(self.invoices)
        self.assertListEqual(
            sorted_invoices.ids, self._get_invoice_ids_from_invoices_path(invoices_path)
        )
        self.assertAttachementCount(self.invoices, 6)

    def test_03(self):
        """
        Data:
            partner_0 with 2 invoices and invoice_sending_method "letter"
            partner_1 with 2 invoice and invoice_sending_method "email"
            partner_2 with 2 invoice and invoice_sending_method "letter"
        Test case:
            Generate the allt invoices before launching the wizard
            Print all the invoices with the wizard
        Expected result:
            * 4 invoices are printed (partner_0 and partner_2) for sending
            method "letter"
            * invoices are sorted by partner's ref and invoice number
        """
        self._generate_invoice_document(self.invoices)
        invoices_path = self._print_invoices(self.invoices)
        self.assertTrue(invoices_path)
        self.assertEqual(4, len(invoices_path))
        sorted_invoices = self._sort_invoices(
            self.invoices.filtered(
                lambda a: a.partner_id in (self.partner_0, self.partner_2)
            )
        )
        self.assertListEqual(
            sorted_invoices.ids, self._get_invoice_ids_from_invoices_path(invoices_path)
        )
        self.assertAttachementCount(self.invoices, 6)
