Odoo/OpenERP Swiss Localization
===============================

This repository hosts official Swiss localization provided by OCA.

It extends Odoo/OpenERP to add needed featues to use Odoo/OpenERP in Switzerland.


l10n_ch_bank
------------

Provides the list of all Swiss banks and their branches with all relative data as clearing, city, etc.


l10n_ch_zip
-----------

Provides the list of all Swiss postal ZIP codes for auto-completion.


l10n_ch_payment_slip
--------------------

Adds ESR/BVR report on invoice. Every ESR/BVR element position can be configured independently by company.
Multiple payment terms on invoices are supported.

It will also allow you to import V11 bank statement files and do an automatical reconciliation.


l10n_ch_base_bank
-----------------

Adds the support of postal account and bank postal account norm.
The partner bank form allows you to input Swiss bank account and postal account in a correct manner.


l10n_ch_dta
-----------

Provides support of DTA payment file protocol to generate electronic payment file.
This feature will be deprecated around the end of 2014.


l10n_ch_sepa
------------

Provides support of SEPA/PAIN electronic payment file.
Only credit transfer files are supported.


l10n_ch_scan_bvr
----------------

Allows you to scan the ESR/BVR references and automatically create the proper supplier invoices.
