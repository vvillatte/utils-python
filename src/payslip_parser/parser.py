import pdfplumber
import re


def clean_money(value):
    if not value:
        return None
    return float(value.replace("$", "").replace(",", "").strip())


def parse_payslip(pdf_path):
    data = {
        "employee": {},
        "pay_info": {},
        "employer": {},
        "job": {},
        "earnings": {},
        "superannuation": {},
        "components": [],
        "bank_payments": [],
        "super_contributions": [],
        "leave_details": [],
        "suggested_filename": None,
    }

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages)

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # ---------------------------
    # BASIC FIELDS
    # ---------------------------

    # Employer
    if "NEUROSCIENCE RESEARCH" in text.upper():
        data["employer"]["name"] = "Neuroscience Research Australia"

    abn = re.search(r"ABN:\s*(\d+)", text)
    if abn:
        data["employer"]["abn"] = abn.group(1)

    # Pay info
    for label, key in [
        ("Period Starting:", "period_start"),
        ("Period Ending:", "period_end"),
        ("Date Paid:", "date_paid"),
    ]:
        m = re.search(label + r"\s*(\d{2}/\d{2}/\d{4})", text)
        if m:
            data["pay_info"][key] = m.group(1)

    # Employee ID
    emp_id = re.search(r"Employee Id:\s*(\d+)", text)
    if emp_id:
        data["employee"]["id"] = emp_id.group(1)

    # ---------------------------
    # EMPLOYEE NAME (merged with Hours Paid)
    # ---------------------------

    for line in lines:
        # Look for "Hours Paid:" merged with name
        if "Hours Paid:" in line:
            m = re.search(r"^(.*?)\s+Hours Paid:", line)
            if m:
                data["employee"]["name"] = m.group(1).strip()
            break

    # ---------------------------
    # JOB + EARNINGS
    # ---------------------------

    for line in lines:
        if line.startswith("Job Title:"):
            data["job"]["title"] = line.split(":", 1)[1].strip()

        elif line.startswith("Base Pay Rate:"):
            data["job"]["base_pay_rate"] = line.split(":", 1)[1].strip()

        elif "Hours Paid:" in line:
            m = re.search(r"Hours Paid:\s*([\d.]+)", line)
            if m:
                data["earnings"]["hours_paid"] = float(m.group(1))

        elif line.startswith("Gross Earnings:"):
            data["earnings"]["gross"] = clean_money(line.split(":", 1)[1])

        elif line.startswith("Net Payment:"):
            data["earnings"]["net"] = clean_money(line.split(":", 1)[1])

        elif line.startswith("Super Payments:"):
            data["superannuation"]["total"] = clean_money(line.split(":", 1)[1])

    # ---------------------------
    # PAY SLIP COMPONENTS
    # ---------------------------

    section = None
    for line in lines:
        if line.startswith("Pay Slip Components"):
            section = "components"
            continue

        if section == "components":
            if line in ["Wages and Earnings", "Pre Tax Deductions", "Taxes", "Superannuation Breakdown"]:
                continue

            # Stop when next section begins
            if line.startswith("Bank Payments"):
                section = None
                continue

            # Parse component rows
            m = re.match(
                r"(.+?)\s+([\d.]+)?\s*\$?([\d.,]+)?\s*\$([\d.,]+)\s*\$([\d.,]+)",
                line
            )
            if m:
                desc, hours, rate, this_pay, ytd = m.groups()
                data["components"].append({
                    "description": desc.strip(),
                    "hours_units": hours,
                    "rate": rate,
                    "this_pay": clean_money(this_pay),
                    "year_to_date": clean_money(ytd),
                })

    # ---------------------------
    # BANK PAYMENTS
    # ---------------------------

    section = None
    for line in lines:
        if line.startswith("Bank Payments"):
            section = "bank"
            continue

        if section == "bank":
            if line.startswith("Super Contributions"):
                section = None
                continue

            m = re.match(r"(.+?)\s+([0-9]+ - \*\*\*\*[0-9]+)\s+\$([\d.,]+)", line)
            if m:
                name, account, amount = m.groups()
                data["bank_payments"].append({
                    "account_name": name.strip(),
                    "account": account.strip(),
                    "amount": clean_money(amount),
                })

    # ---------------------------
    # SUPER CONTRIBUTIONS
    # ---------------------------

    section = None
    for line in lines:
        if line.startswith("Super Contributions"):
            section = "super_contrib"
            continue

        if section == "super_contrib":
            if line.startswith("Employee Id"):
                section = None
                continue

            m = re.match(r"(.+?)\s+(.+?)\s+(\*\*\*\*.+?)\s+\$([\d.,]+)", line)
            if m:
                fund, category, member, amount = m.groups()
                data["super_contributions"].append({
                    "fund": fund.strip(),
                    "category": category.strip(),
                    "member_number": member.strip(),
                    "amount": clean_money(amount),
                })

    # ---------------------------
    # LEAVE DETAILS (page 2)
    # ---------------------------

    for line in lines:
        m = re.match(
            r"(Annual Leave|Personal/Carer's Leave)\s+([\d.]+ hours)\s+([\d.]+ hours)\s+([\d.]+ hours)",
            line
        )
        if m:
            leave_type, accrued, taken, remaining = m.groups()
            data["leave_details"].append({
                "type": leave_type,
                "accrued": accrued,
                "taken": taken,
                "remaining": remaining,
            })

    # ---------------------------
    # SUGGESTED FILENAME
    # ---------------------------

    try:
        dd, mm, yyyy = data["pay_info"]["date_paid"].split("/")
        iso_date = f"{yyyy}-{mm}-{dd}"

        net = data["earnings"]["net"]
        net_fmt = f"AUD {net:,.2f}"

        employer = data["employer"]["name"]
        employee = data["employee"]["name"]

        data["suggested_filename"] = (
            f"{iso_date} - {net_fmt} - {employer} - payslip - {employee}"
        )
    except Exception:
        data["suggested_filename"] = None

    return data
