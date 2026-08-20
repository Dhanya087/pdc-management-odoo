# PDC Management for Odoo 18

PDC Management is an Odoo 18 module for managing **Post-Dated Cheques (PDC)**, including cheque records, payees, bank details, cheque status tracking, and a management dashboard.

## Features

* **PDC Cheque Management**

  * Create and manage post-dated cheques
  * Track cheque number, amount, date, bank, payee, and status
  * Manage cheque lifecycle and status changes

* **Bank Management**

  * Maintain bank details
  * Link banks with PDC cheque records

* **Payee Management**

  * Create and manage payees
  * Link payees to cheque records

* **Cheque Status Management**

  * Track cheque status
  * Manage failed/returned cheques
  * Record failure information

* **PDC Dashboard**

  * Dashboard for monitoring PDC records
  * Overview of cheque information and status

* **Automatic Processing**

  * Scheduled actions for PDC processing
  * Automatic sequence generation for cheque records

## Technical Details

| Item         | Details              |
| ------------ | -------------------- |
| Odoo Version | 18.0                 |
| Module Name  | `pdc_management`     |
| Framework    | Odoo                 |
| Backend      | Python               |
| Frontend     | XML, JavaScript, CSS |
| Database     | PostgreSQL           |

## Module Structure

```text
pdc_management/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── pdc_cron.xml
│   └── pdc_sequence.xml
├── models/
│   ├── __init__.py
│   ├── pdc_bank.py
│   ├── pdc_cheque.py
│   └── pdc_payee.py
├── security/
│   ├── ir.model.access.csv
│   └── pdc_security.xml
├── static/
│   └── src/
│       ├── css/
│       ├── js/
│       └── xml/
├── views/
│   ├── pdc_bank_views.xml
│   ├── pdc_cheque_views.xml
│   ├── pdc_dashboard_views.xml
│   ├── pdc_fail_wizard_views.xml
│   ├── pdc_menu.xml
│   └── pdc_payee_views.xml
└── wizards/
    ├── __init__.py
    └── pdc_fail_wizard.py
```

## Installation

1. Copy the `pdc_management` module into your Odoo custom addons directory.

2. Make sure the directory is included in your Odoo `addons_path`.

3. Restart the Odoo server.

4. Activate developer mode.

5. Go to:

```text
Apps → Update Apps List
```

6. Search for:

```text
PDC Management
```

7. Click **Install**.

## Usage

After installation, open the PDC Management menu from the Odoo interface.

You can then:

1. Configure bank details.
2. Create payees.
3. Create PDC cheque records.
4. Track cheque status.
5. Manage failed/returned cheques.
6. Monitor PDC information through the dashboard.

## Requirements

* Odoo 18 Community/compatible Odoo 18 environment
* PostgreSQL
* Python dependencies required by the Odoo installation

## Configuration

Configure the required banks, payees, access rights, and PDC settings before creating cheque records.

## License

Add the license applicable to your project here.

> **Note:** If this module is based on or derived from employer/client code, verify that you have permission to publish and redistribute it before making this repository public.

## Author

**Dhanya**

## Disclaimer

This project is intended for demonstration and learning purposes. Always verify the module's compatibility with your specific Odoo 18 environment before using it in production.
