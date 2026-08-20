# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)


class PdcCheque(models.Model):
    _name = 'pdc.cheque'
    _description = 'Post Dated Cheque'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'cheque_date asc, id desc'
    _check_company_auto = True

    # ─────────────────────────── Identification ───────────────────────────
    name = fields.Char(string='Reference', readonly=True, default='New', copy=False, tracking=True)
    cheque_number = fields.Char(string='Cheque Number', required=True, tracking=True, copy=False)

    # ─────────────────────────── Dates ────────────────────────────────────
    entered_date = fields.Date(string='Issued Date', default=fields.Date.today, readonly=True)
    cheque_date = fields.Date(string='Cheque Date (Due Date)', required=True, tracking=True)

    # ─────────────────────────── Relations ────────────────────────────────
    bank_id = fields.Many2one('res.partner.bank', string='Bank Account', required=True, tracking=True,
                              check_company=True)
    payee_id = fields.Many2one('pdc.payee', string='Payee', required=True, tracking=True)
    entered_by = fields.Many2one('res.users', string='Issued By', default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,
                                 readonly=True)

    # ─────────────────────────── Financial ────────────────────────────────
    amount = fields.Float(string='Amount', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True)

    # ─────────────────────────── Status ───────────────────────────────────
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    processing_timeline = fields.Selection([
        ('15_days', 'Processing in 15 Days'),
        ('7_days', 'Processing in 7 Days'),
        ('today', 'Due Today'),
        ('overdue', 'Overdue'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled'),
        ('future', 'Future'),
    ], string='Processing Timeline', compute='_compute_processing_timeline', store=True)

    days_to_due = fields.Integer(string='Days to Due Date', compute='_compute_days_to_due', store=True)

    # ─────────────────────────── Scanned Cheque ───────────────────────────
    scanned_cheque = fields.Binary(string='Scanned Cheque', attachment=True)
    scanned_cheque_filename = fields.Char(string='File Name')
    scanned_cheque_url = fields.Char(string='Open File', compute='_compute_scanned_cheque_url')
    is_pdf_upload = fields.Boolean(string='Is PDF', compute='_compute_scanned_cheque_url', store=False)

    # ─────────────────────────── Notes ────────────────────────────────────
    notes = fields.Text(string='Notes / Remarks')
    failure_reason = fields.Text(string='Cancellation Reason', tracking=True)

    # ─────────────────────────── Misc ─────────────────────────────────────
    show_image = fields.Boolean(string='Show Image', default=False)

    # ─────────────────────────── Computed from res.partner.bank ───────────
    bank_account_number = fields.Char(related='bank_id.acc_number', string='Account Number', store=True)
    bank_ifsc = fields.Char(related='bank_id.bank_bic', string='IFSC / BIC Code')
    bank_branch = fields.Char(related='bank_id.bank_id.name', string='Bank Name')
    payee_name = fields.Char(related='payee_id.name', string='Payee Name', store=True)

    # ═══════════════════════════ HELPERS ══════════════════════════════════

    @staticmethod
    def _currency_code_for_company(company):
        country_code = company.country_id.code or ''
        company_name = company.name or ''
        if country_code == 'QA' or 'W.L.L' in company_name:
            return 'QAR'
        elif country_code == 'AE' or 'L.L.C' in company_name:
            return 'AED'
        elif country_code == 'OM' or 'LLC' in company_name:
            return 'OMR'
        return 'QAR'

    def _get_company_domain(self):
        return [('company_id', '=', self.env.company.id)]

    # ═══════════════════════════ COMPUTES ═════════════════════════════════

    @api.depends('company_id')
    def _compute_currency_id(self):
        for rec in self:
            company = rec.company_id or self.env.company
            code = self._currency_code_for_company(company)
            currency = self.env['res.currency'].search(
                [('name', '=', code), ('active', 'in', [True, False])], limit=1)
            rec.currency_id = currency or company.currency_id

    @api.depends('cheque_date', 'status')
    def _compute_days_to_due(self):
        today = date.today()
        for rec in self:
            rec.days_to_due = (rec.cheque_date - today).days if rec.cheque_date else 0

    @api.depends('cheque_date', 'status', 'days_to_due')
    def _compute_processing_timeline(self):
        for rec in self:
            if rec.status == 'processed':
                rec.processing_timeline = 'processed'
            elif rec.status == 'cancelled':
                rec.processing_timeline = 'cancelled'
            elif rec.cheque_date:
                days = rec.days_to_due
                if days < 0:
                    rec.processing_timeline = 'overdue'
                elif days == 0:
                    rec.processing_timeline = 'today'
                elif days <= 7:
                    rec.processing_timeline = '7_days'
                elif days <= 15:
                    rec.processing_timeline = '15_days'
                else:
                    rec.processing_timeline = 'future'
            else:
                rec.processing_timeline = 'future'

    @api.depends('scanned_cheque', 'scanned_cheque_filename')
    def _compute_scanned_cheque_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            if rec.scanned_cheque and rec.id:
                filename = rec.scanned_cheque_filename or 'cheque'
                rec.scanned_cheque_url = (
                        "%s/web/content/pdc.cheque/%d/scanned_cheque/%s?download=false"
                        % (base_url, rec.id, filename)
                )
                rec.is_pdf_upload = filename.lower().endswith('.pdf')
            else:
                rec.scanned_cheque_url = False
                rec.is_pdf_upload = False

    # ═══════════════════════════ DATE VALIDATION ══════════════════════════

    @api.constrains('cheque_date', 'entered_date')
    def _check_cheque_date(self):
        for rec in self:
            if not rec.cheque_date:
                continue
            issue_date = rec.entered_date or date.today()
            if rec.cheque_date <= issue_date:
                raise ValidationError(
                    _("Cheque Due Date must be after the Issued Date (%s).\n"
                      "You cannot select today or any past date.") % issue_date
                )
            if rec.cheque_date.year > issue_date.year:
                raise ValidationError(
                    _("Cheque Due Date cannot go beyond the year %s.\n"
                      "Maximum allowed date is 31/12/%s.")
                    % (issue_date.year, issue_date.year)
                )

    # ═══════════════════════════ ORM OVERRIDES ════════════════════════════

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pdc.cheque') or 'New'
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super().create(vals_list)

    def write(self, vals):
        # ── Fields that are always allowed to change regardless of status ──
        always_allowed = {
            'status', 'processing_timeline', 'days_to_due',
            'failure_reason', 'show_image', 'message_ids',
            'activity_ids', 'scanned_cheque_url', 'is_pdf_upload',
        }
        locked_statuses = ('active', 'processed', 'cancelled')
        for rec in self:
            if rec.status in locked_statuses:
                blocked = set(vals.keys()) - always_allowed
                if blocked:
                    raise UserError(
                        _("⚠️ This cheque is locked and cannot be edited.\n\n"
                          "Once a cheque is Activated, its details cannot be modified.\n\n"
                          "If changes are required, please Cancel this cheque and create a new one.")
                    )
        return super().write(vals)

    # ═══════════════════════════ ACTIONS / BUTTONS ════════════════════════

    def action_set_active(self):
        for rec in self:
            if rec.status != 'draft':
                raise UserError(_("Only Draft cheques can be Activated."))
            # ── Amount must be > 0 ──────────────────────────────────────
            if not rec.amount or rec.amount <= 0:
                raise UserError(
                    _("⚠️ Cannot Activate Cheque!\n\n"
                      "The cheque amount must be greater than 0.\n"
                      "Current amount: %s\n\n"
                      "Please enter a valid amount before activating.")
                    % rec.amount
                )
            rec.status = 'active'
            rec.message_post(body=_("Cheque activated."))

    def action_set_processed(self):
        for rec in self:
            if rec.status not in ('draft', 'active'):
                raise UserError(_("Only Draft or Active cheques can be marked as Processed."))
            rec.status = 'processed'
            rec.processing_timeline = 'processed'
            rec.message_post(body=_("Cheque successfully processed."))

    def action_cancel(self):
        self.ensure_one()
        return {
            'name': _('Cancel Cheque'),
            'type': 'ir.actions.act_window',
            'res_model': 'pdc.fail.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cheque_id': self.id},
        }

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Attachments'),
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    def action_toggle_image(self):
        for rec in self:
            rec.show_image = not rec.show_image

    def action_open_scanned_cheque(self):
        self.ensure_one()
        if not self.scanned_cheque_url:
            raise UserError(_("No file has been uploaded yet."))
        return {'type': 'ir.actions.act_url', 'url': self.scanned_cheque_url, 'target': 'new'}

    # ═══════════════════════════ CRON / ALERTS ════════════════════════════

    @api.model
    def _cron_update_processing_timeline(self):
        cheques = self.sudo().search([('status', 'in', ('draft', 'active'))])
        cheques._compute_days_to_due()
        cheques._compute_processing_timeline()
        _logger.info("PDC: Updated processing timeline for %d cheques.", len(cheques))

    @api.model
    def _cron_send_alerts(self):
        today = date.today()
        day_15 = today + timedelta(days=15)
        day_7 = today + timedelta(days=7)

        cheques_15 = self.sudo().search([('cheque_date', '=', day_15), ('status', 'in', ('draft', 'active'))])
        for cheque in cheques_15:
            cheque.message_post(
                body=_("Alert: Cheque %s is due in 15 days (%s). Amount: %s") % (cheque.cheque_number,
                                                                                 cheque.cheque_date, cheque.amount),
                subject=_("PDC Alert - 15 Days to Due Date"), subtype_xmlid='mail.mt_note')
            self._send_activity(cheque, days=15)

        cheques_7 = self.sudo().search([('cheque_date', '=', day_7), ('status', 'in', ('draft', 'active'))])
        for cheque in cheques_7:
            cheque.message_post(
                body=_("Alert: Cheque %s is due in 7 days (%s). Amount: %s") % (cheque.cheque_number,
                                                                                cheque.cheque_date, cheque.amount),
                subject=_("PDC Alert - 7 Days to Due Date"), subtype_xmlid='mail.mt_note')
            self._send_activity(cheque, days=7)

        cheques_today = self.sudo().search([('cheque_date', '=', today), ('status', 'in', ('draft', 'active'))])
        for cheque in cheques_today:
            cheque.message_post(
                body=_("Alert: Cheque %s is DUE TODAY! Amount: %s") % (cheque.cheque_number, cheque.amount),
                subject=_("PDC Alert - Due Today"), subtype_xmlid='mail.mt_note')

        overdue_cheques = self.sudo().search([('cheque_date', '<', today), ('status', 'in', ('draft', 'active'))])
        for cheque in overdue_cheques:
            cheque.message_post(
                body=_(
                    "URGENT: Cheque %s was due on %s and has NOT been processed! Amount: %s — Please process immediately!")
                     % (cheque.cheque_number, cheque.cheque_date, cheque.amount),
                subject=_("PDC OVERDUE ALERT - Immediate Action Required"), subtype_xmlid='mail.mt_note')

        _logger.info("PDC Alerts sent: 15-day=%d, 7-day=%d, today=%d, overdue=%d",
                     len(cheques_15), len(cheques_7), len(cheques_today), len(overdue_cheques))

    def _send_activity(self, cheque, days):
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return
        existing = self.env['mail.activity'].search([
            ('res_model', '=', 'pdc.cheque'), ('res_id', '=', cheque.id),
            ('activity_type_id', '=', activity_type.id)])
        if not existing:
            cheque.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=cheque.cheque_date,
                summary=_("Process cheque %s (due in %d days)") % (cheque.cheque_number, days),
                user_id=cheque.entered_by.id or self.env.user.id)

    # ═══════════════════════════ DASHBOARD DATA ═══════════════════════════

    @api.model
    def get_dashboard_data(self):
        today = date.today()
        day_7 = today + timedelta(days=7)
        day_15 = today + timedelta(days=15)
        company_domain = [('company_id', '=', self.env.company.id)]

        def count_and_amount(domain):
            recs = self.search(company_domain + domain)
            return {'count': len(recs), 'amount': sum(recs.mapped('amount'))}

        return {
            'in_progress': count_and_amount([('status', 'in', ('draft', 'active'))]),
            'due_today': count_and_amount(
                [('cheque_date', '=', today), ('status', 'not in', ('processed', 'cancelled'))]),
            'due_7_days': count_and_amount([('cheque_date', '>', today), ('cheque_date', '<=', day_7),
                                            ('status', 'not in', ('processed', 'cancelled'))]),
            'due_15_days': count_and_amount([('cheque_date', '>', day_7), ('cheque_date', '<=', day_15),
                                             ('status', 'not in', ('processed', 'cancelled'))]),
            'overdue': count_and_amount(
                [('cheque_date', '<', today), ('status', 'not in', ('processed', 'cancelled'))]),
            'processed': count_and_amount([('status', '=', 'processed')]),
            'cancelled': count_and_amount([('status', '=', 'cancelled')]),
        }

    @api.model
    def get_dashboard_rows(self, view, bank=None, month=None):
        today = date.today()
        domains = {
            'overdue': [('cheque_date', '<', today), ('status', 'not in', ['processed', 'cancelled'])],
            'today': [('cheque_date', '=', today), ('status', 'not in', ['processed', 'cancelled'])],
            'due_7': [('cheque_date', '>', today), ('cheque_date', '<=', today + timedelta(days=7)),
                      ('status', 'not in', ['processed', 'cancelled'])],
            'due_15': [('cheque_date', '>', today + timedelta(days=7)),
                       ('cheque_date', '<=', today + timedelta(days=15)),
                       ('status', 'not in', ['processed', 'cancelled'])],
            'processed': [('status', '=', 'processed')],
            'cancelled': [('status', '=', 'cancelled')],
            'in_prog': [('status', 'in', ['draft', 'active'])],
        }
        company_domain = [('company_id', '=', self.env.company.id)]
        domain = company_domain + domains.get(view, [])
        recs = self.search(domain, order='cheque_date asc')
        return [{
            'id': r.id, 'name': r.name, 'cheque_number': r.cheque_number,
            'payee': r.payee_id.name or '', 'bank': r.bank_id.bank_id.name or '',
            'amount': r.amount, 'date': str(r.cheque_date) if r.cheque_date else '',
            'status': r.status,
        } for r in recs]

    @api.model
    def get_company_currency_info(self):
        company = self.env.company
        code = self._currency_code_for_company(company)
        country_code = company.country_id.code or ''
        company_name = company.name or ''
        if country_code == 'QA' or 'W.L.L' in company_name:
            display_code = 'QA'
        elif country_code == 'AE' or 'L.L.C' in company_name:
            display_code = 'AE'
        elif country_code == 'OM' or 'LLC' in company_name:
            display_code = 'OM'
        else:
            display_code = 'QA'
        return {'symbol': code, 'code': display_code}
