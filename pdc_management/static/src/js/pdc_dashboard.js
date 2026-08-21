/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PDCDashboard extends Component {
    setup() {
        this.orm    = useService("orm");
        this.action = useService("action");

        this.state = useState({
            // KPIs
            in_progress_count: 0,   in_progress_amount: 0,
            due_today_count: 0,     due_today_amount: 0,
            due_7_days_count: 0,    due_7_days_amount: 0,
            due_15_days_count: 0,   due_15_days_amount: 0,
            overdue_count: 0,       overdue_amount: 0,
            processed_count: 0,     processed_amount: 0,
            cancelled_count: 0,     cancelled_amount: 0,

            // Currency
            currencySymbol: "QAR",
            countryCode: "QA",

            // Table
            selectedView:  null,
            tableRows:     [],
            filteredRows:  [],
            tableLoading:  false,
            filterBank:    "all",
            filterMonth:   "all",
            filterSearch:  "",
        });

        onWillStart(async () => {
            await Promise.all([
                this._loadKPIs(),
                this._loadCurrency(),
            ]);
        });
    }

    // ── Load currency info based on company country ───────────────────────

    async _loadCurrency() {
        try {
            const info = await this.orm.call("pdc.cheque", "get_company_currency_info", []);
            if (info) {
                this.state.currencySymbol = info.symbol || "QAR";
                this.state.countryCode    = info.code   || "QA";
            }
        } catch (e) {
            console.error("Currency load error:", e);
        }
    }

    // ── Load KPI card data ────────────────────────────────────────────────

    async _loadKPIs() {
        try {
            const data = await this.orm.call("pdc.cheque", "get_dashboard_data", []);
            if (data) {
                this.state.in_progress_count  = data.in_progress?.count  || 0;
                this.state.in_progress_amount = data.in_progress?.amount || 0;
                this.state.due_today_count    = data.due_today?.count    || 0;
                this.state.due_today_amount   = data.due_today?.amount   || 0;
                this.state.due_7_days_count   = data.due_7_days?.count   || 0;
                this.state.due_7_days_amount  = data.due_7_days?.amount  || 0;
                this.state.due_15_days_count  = data.due_15_days?.count  || 0;
                this.state.due_15_days_amount = data.due_15_days?.amount || 0;
                this.state.overdue_count      = data.overdue?.count      || 0;
                this.state.overdue_amount     = data.overdue?.amount     || 0;
                this.state.processed_count    = data.processed?.count    || 0;
                this.state.processed_amount   = data.processed?.amount   || 0;
                this.state.cancelled_count    = data.cancelled?.count    || 0;
                this.state.cancelled_amount   = data.cancelled?.amount   || 0;
            }
        } catch (e) {
            console.error("KPI load error:", e);
        }
    }

    // ── Filters ───────────────────────────────────────────────────────────

    _resetFilters() {
        this.state.filterBank   = "all";
        this.state.filterMonth  = "all";
        this.state.filterSearch = "";
    }

    _applyFilters() {
        let rows = [...this.state.tableRows];
        if (this.state.filterBank !== "all") {
            rows = rows.filter((r) => r.bank === this.state.filterBank);
        }
        if (this.state.filterMonth !== "all") {
            rows = rows.filter((r) => r.date && r.date.substring(0, 7) === this.state.filterMonth);
        }
        const q = this.state.filterSearch.trim().toLowerCase();
        if (q) {
            rows = rows.filter(
                (r) =>
                    (r.name          || "").toLowerCase().includes(q) ||
                    (r.payee         || "").toLowerCase().includes(q) ||
                    (r.cheque_number || "").toLowerCase().includes(q)
            );
        }
        this.state.filteredRows = rows;
    }

    // ── Card click ────────────────────────────────────────────────────────

    onCardClick(view) {
        if (this.state.selectedView === view) {
            this.state.selectedView = null;
            this.state.tableRows    = [];
            this.state.filteredRows = [];
            this._resetFilters();
            return;
        }
        this.state.selectedView = view;
        this._resetFilters();
        this.state.tableLoading = true;
        this.state.tableRows    = [];
        this.state.filteredRows = [];

        this.orm
            .call("pdc.cheque", "get_dashboard_rows", [view])
            .then((rows) => {
                this.state.tableRows    = rows || [];
                this.state.filteredRows = rows || [];
                this.state.tableLoading = false;
            })
            .catch((e) => {
                console.error("Table load error:", e);
                this.state.tableLoading = false;
            });
    }

    // ── Row click — open form view ────────────────────────────────────────

    onRowClick(recordId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "pdc.cheque",
            res_id: recordId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ── Panel close ───────────────────────────────────────────────────────

    onClosePanel() {
        this.state.selectedView = null;
        this.state.tableRows    = [];
        this.state.filteredRows = [];
        this._resetFilters();
    }

    // ── Filter event handlers ─────────────────────────────────────────────

    onBankChange(ev) {
        this.state.filterBank = ev.target.value;
        this._applyFilters();
    }

    onMonthChange(ev) {
        this.state.filterMonth = ev.target.value;
        this._applyFilters();
    }

    onSearchInput(ev) {
        this.state.filterSearch = ev.target.value;
        this._applyFilters();
    }

    // ── Template helpers ──────────────────────────────────────────────────

    formatAmount(amount) {
        if (!amount && amount !== 0) return "—";
        // Format with 3 decimal places for Gulf currencies (QAR/AED/OMR)
        const decimals = this.state.countryCode === "OM" ? 3 : 2;
        const formatted = Number(amount).toLocaleString("en-US", {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });
        return `${this.state.currencySymbol} ${formatted}`;
    }

    formatDate(dateStr) {
        if (!dateStr) return "—";
        const [y, m, d] = dateStr.split("-");
        return `${d}/${m}/${y}`;
    }

    getTotalAmount() {
        return this.state.filteredRows.reduce((s, r) => s + (r.amount || 0), 0);
    }

    getUniqueBanks() {
        return [...new Set(this.state.tableRows.map((r) => r.bank).filter(Boolean))].sort();
    }

    getUniqueMonths() {
        return [
            ...new Set(
                this.state.tableRows
                    .map((r) => (r.date ? r.date.substring(0, 7) : null))
                    .filter(Boolean)
            ),
        ].sort();
    }

    monthLabel(ym) {
        if (!ym) return "";
        const [y, m] = ym.split("-");
        return new Date(y, m - 1).toLocaleString("default", { month: "short", year: "numeric" });
    }

    getViewLabel() {
        const labels = {
            overdue:   "Overdue",
            today:     "Due Today",
            due_7:     "Due in 7 Days",
            due_15:    "Due in 15 Days",
            in_prog:   "In Progress",
            processed: "Processed",
            cancelled: "Cancelled",
        };
        return labels[this.state.selectedView] || "";
    }

    getBadgeClass(status) {
        const map = {
            active:    "badge-active",
            draft:     "badge-draft",
            processed: "badge-processed",
            cancelled: "badge-cancelled",
        };
        return map[status] || "badge-draft";
    }

    isActiveCard(view) {
        return this.state.selectedView === view;
    }

    // Country flag emoji for header display
    getCountryFlag() {
        const flags = { QA: "🇶🇦", AE: "🇦🇪", OM: "🇴🇲" };
        return flags[this.state.countryCode] || "";
    }
}

PDCDashboard.template = "pdc_management.pdc_dashboard_template";
registry.category("actions").add("pdc_dashboard", PDCDashboard);