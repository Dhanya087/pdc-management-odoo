# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PdcBank(models.Model):
    _name = 'pdc.bank'
    _description = 'PDC Bank Details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'bank_name'
    _order = 'bank_name asc'

    bank_name = fields.Char(
        string='Bank Name',
        required=True,
        tracking=True,
    )
    account_number = fields.Char(
        string='Account Number',
        required=True,
        tracking=True,
    )
    ifsc_code = fields.Char(
        string='IFSC Code',
        required=True,
        tracking=True,
    )
    branch = fields.Char(
        string='Branch',
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')

    @api.constrains('account_number')
    def _check_account_number(self):
        for rec in self:
            domain = [
                ('account_number', '=', rec.account_number),
                ('id', '!=', rec.id),
            ]
            if self.search(domain):
                raise ValidationError(
                    f"Account Number '{rec.account_number}' already exists!"
                )