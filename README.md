# Insurance CRM

A Python-based desktop CRM built to simplify insurance agency operations, reduce repetitive administrative work, and make policy and commission management more organized.

This project demonstrates how a real-world business workflow can be translated into a desktop application, combining data management, business rules, automated calculations, Excel integration, and reporting.

## The Problem

Insurance agencies often manage large volumes of customer records, insurance policies, collections, and commission calculations. Handling these tasks manually across separate files can lead to repetitive work, inconsistent data, and time-consuming reporting.

## The Solution

Insurance CRM brings key insurance workflows into one application, helping organize operational data and simplify routine tasks.

## Key Features

- **Customer Management:** Maintain and search insurance customer records.
- **Insurance Policy Management:** Manage policy information, search records, and work with policy data in one place.
- **Marketer Management:** Manage marketers and configure commission rules.
- **Commission Calculations:** Apply business rules to commission calculations and generate commission reports.
- **Excel Integration:** Import insurance policies and collection records from Excel files.
- **Reporting and Export:** Generate reports and export data for further analysis in Excel.
- **Operational Dashboard:** View a summary of key operational information.
- **Persian and Jalali Date Support:** Support Persian-language workflows and the Jalali calendar.

## Technology Stack

- **Language:** Python 3.13
- **Desktop UI:** Tkinter
- **ORM and Database:** SQLAlchemy, SQLite
- **Database Migrations:** Alembic
- **Data Processing and Excel:** Pandas, OpenPyXL
- **Charts:** Matplotlib
- **Jalali Calendar:** jdatetime

## What This Project Demonstrates

- Building a desktop application around real business requirements
- Organizing application logic into separate services and UI components
- Working with relational data and database models
- Implementing business-specific calculation rules
- Integrating Excel import and export workflows
- Developing reporting features for operational use
- Supporting Persian text and Jalali dates in a desktop application

## Installation and Setup

### Prerequisites

- Python 3.13
- Git (if cloning the repository)

### 1. Clone the repository

```bash
git clone https://github.com/Mohsen-hmaa/insurance-crm.git
cd insurance-crm
```

Alternatively, download the repository as a ZIP file and extract it.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```bat
venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Run the application

```bash
python main.py
```

On first launch, the application initializes the database and prompts the user to create the initial System Admin account if no users exist. Subsequent launches proceed to the regular login screen.

## Data and Privacy

This repository is intended for demonstration and portfolio purposes. Real customer records, insurance policy data, production databases, and private business files should not be committed to the repository.

Use test data when evaluating the application.

## Project Status

This is a practical portfolio project developed around insurance agency workflows. Its focus is on improving day-to-day data management, reducing repetitive administrative tasks, and making insurance operations easier to organize.

## Disclaimer

Insurance CRM is an independent software project designed for insurance workflow management. It is not affiliated with or endorsed by any insurance company.
