# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PdcPayee(models.Model):
    _name = 'pdc.payee'
    _description = 'PDC Payee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'name asc'
    _check_company_auto = True  # ← enforce company isolation

    name = fields.Char(
        string='Payee Name',
        required=True,
        tracking=True,
    )
    contact_number = fields.Char(string='Contact Number')
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    active = fields.Boolean(default=True)

    # ── Multi-company field ──────────────────────────────────────
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Linked Contact',
        help='Link to an existing Odoo contact',
    )
    cheque_ids = fields.One2many(
        'pdc.cheque', 'payee_id',
        string='Cheques',
    )
    cheque_count = fields.Integer(
        string='Total Cheques',
        compute='_compute_cheque_count',
    )
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
    )
    notes = fields.Text(string='Notes')

    @api.depends('cheque_ids')
    def _compute_cheque_count(self):
        for rec in self:
            rec.cheque_count = len(rec.cheque_ids)

    @api.depends('cheque_ids.amount', 'cheque_ids.status')
    def _compute_total_amount(self):
        for rec in self:
            active_cheques = rec.cheque_ids.filtered(
                lambda c: c.status not in ('failed',)
            )
            rec.total_amount = sum(active_cheques.mapped('amount'))

    def action_view_cheques(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Cheques - {self.name}',
            'res_model': 'pdc.cheque',
            'view_mode': 'list,form',
            'domain': [('payee_id', '=', self.id)],
            'context': {'default_payee_id': self.id},
        }