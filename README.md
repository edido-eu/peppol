# Exchange UBL documents with the Edido.EU peppol gateway

## UBL Invoice Generation

Generate UBL document with the OCA modules

Install the module and its dependencies:
* https://github.com/OCA/edi/tree/16.0/account_invoice_ubl
* https://github.com/edido-eu/peppol/tree/16.0/base_ubl_payment_mode_required

Set UNECE codes on the taxes:
* For VAT, use categ "S", type "VAT"
* For taxes without VAT, use "E", type "OTH"

In the settings:
* enable "Payment mode required for UBL documents"
* enable "Embed PDF in UBL XML Invoice"
* set "Select Format (XML format attached to your PDF customer invoices)" to "None" 

## UBL Invoice Sending

Install the python library required by base_view_inheritance_extension
* astor

Install the modules:
* https://github.com/OCA/server-tools/tree/16.0/base_view_inheritance_extension
* https://github.com/OCA/account-invoicing/tree/16.0/account_invoice_transmit_method
* https://github.com/edido-eu/peppol/tree/16.0/account_invoice_export_ubl

In the menu Settings > Technical > Peppol Server, configure the edido.eu gateway:
* Production Peppol network: api.edido.eu
* Test Peppol network: test.edido.eu

In the Accounting/Invoicing settings, section "Electronic Invoices", select the peppol server to use.

On the customer, sales tab, set the invoice transmit method to peppol.
For self-billing, on the supplier, purchase tab, set the invoice receive method to peppol.

When the invoice is posted, you should have a new button "SEND PEPPOL" in the header of the invoice.

### BBA structured communication

The stored payment reference contains + and / characters that must be removed in the UBL document payment reference. For this purpose, you can install:
* https://github.com/edido-eu/peppol/tree/16.0/l10n_be_account_einvoice_generate
that depends on:
* https://github.com/OCA/bank-payment/tree/16.0/account_payment_order

### Mass sending

Install the modules:
* https://github.com/OCA/account-invoicing/tree/16.0/account_invoice_transmit
  * https://github.com/OCA/account-invoicing/pull/1715
* https://github.com/edido-eu/peppol/tree/16.0/account_invoice_transmit_peppol
