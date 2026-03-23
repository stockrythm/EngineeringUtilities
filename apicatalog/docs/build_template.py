#!/usr/bin/env python3
"""
build_template.py — Integration COE API Catalog
================================================
Generates api-catalog-template.xlsx — the BA data collection workbook.

Usage:
  python3 build_template.py
  python3 build_template.py --output my-template.xlsx

Requirements:
  pip install openpyxl
"""

import argparse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.comments import Comment

C = {
    "navy":    "0D1829", "blue":    "1E3A5F",
    "req_bg":  "FFF7ED", "req_bd":  "FED7AA",
    "opt_bg":  "F0FDF4", "opt_bd":  "BBF7D0",
    "hdr_api": "1E3A5F", "hdr_dep": "312E81",
    "hdr_gw":  "164E63", "hdr_mig": "713F12",
    "hdr_coe": "1F2937",
}

def fill(hex_col):
    return PatternFill("solid", start_color=str(hex_col), end_color=str(hex_col))

def fnt(bold=False, color="000000", size=10, italic=False):
    return Font(bold=bold, color=color, size=size, italic=italic, name="Arial")

def bdr(color="CBD5E1"):
    s = Side(style="thin", color=color)
    return Border(left=s, right=s, top=s, bottom=s)

def ctr():
    return Alignment(horizontal="center", vertical="center", wrap_text=True)

def lft(wrap=True):
    return Alignment(horizontal="left", vertical="center", wrap_text=wrap)

def hdr_cell(cell, bg, size=9):
    cell.fill = fill(bg)
    cell.font = fnt(bold=True, color="FFFFFF", size=size)
    cell.alignment = ctr()
    cell.border = bdr("334155")

def req_cell(cell):
    cell.fill = fill(C["req_bg"])
    cell.font = fnt(color="431407")
    cell.alignment = lft()
    cell.border = bdr(C["req_bd"])

def opt_cell(cell):
    cell.fill = fill(C["opt_bg"])
    cell.font = fnt(color="14532D")
    cell.alignment = lft()
    cell.border = bdr(C["opt_bd"])

def add_dv(ws, vals, sqref, title=""):
    joined = '","'.join(vals)
    formula = '"' + joined + '"'
    dv = DataValidation(
        type="list", formula1=formula, allow_blank=True,
        showDropDown=False, showErrorMessage=True,
        errorTitle="Invalid value", error="Please select from the list.",
        showInputMessage=True, promptTitle=title or "Select",
        prompt="Choose a value from the dropdown list"
    )
    ws.add_data_validation(dv)
    dv.sqref = sqref

REF = {
    "layers":       ["EAPI","PAPI","SAPI","BATCH","EVENT","UTILITY","FACADE"],
    "protocols":    ["REST","SOAP","Kafka","AsyncAPI","GraphQL","SFTP","JMS","Other"],
    "runtimes":     ["MuleSoft 4.1","MuleSoft 4.2","MuleSoft 4.3","MuleSoft 4.4",
                     "MuleSoft 4.5","MuleSoft 4.6","MuleSoft 4.7","MuleSoft 4.8",
                     "MuleSoft 4.9","MuleSoft 3.9 (Legacy)"],
    "runtime_types":["AWS Egress Runtime","AWS Ingress Runtime","IGZ Egress",
                     "IGZ Ingress","Qsystem","Process","Experience","System"],
    "java":         ["Java 8","Java 11","Java 17","Java 21"],
    "deploy":       ["OnPrem","AWS","Azure","Hybrid","CloudHub"],
    "status":       ["Active","Deprecated","Inactive","Review"],
    "mig_status":   ["Not Started","In Analysis","In Progress","Blocked",
                     "Complete","Decommission Candidate"],
    "complexity":   ["Low","Medium","High"],
    "waves":        ["Wave 1","Wave 2","Wave 3","Unassigned"],
    "auth":         ["OAuth 2.0 (Client Credentials)","OAuth 2.0 (Auth Code)",
                     "mTLS","Basic Auth","API Key","None","Other"],
    "tls":          ["TLS 1.2","TLS 1.3"],
    "data_class":   ["Public","Internal","Confidential","Restricted"],
    "tribes":       ["Payments","Customer","Cards",
                     "Commercial Digital Channel","Retail Digital Channel","Homebuying"],
    "dep_dir":      ["Consumer (calls this API)","Upstream (this API calls it)"],
    "pol_scope":    ["API Manager","Kafka / API Manager",
                     "Custom policy asset - Exchange"],
    "yes_no":       ["Yes","No"],
}

ROWS = 200


def banner(ws, title, subtitle, bg, num_cols):
    ws.row_dimensions[1].height = 34
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 16
    lc = get_column_letter(num_cols)
    ws.merge_cells("A1:" + lc + "1")
    c = ws["A1"]
    c.value = title
    c.fill = fill(bg)
    c.font = fnt(bold=True, color="FFFFFF", size=13)
    c.alignment = ctr()
    ws.merge_cells("A2:" + lc + "2")
    c = ws["A2"]
    c.value = subtitle
    c.fill = fill(bg)
    c.font = fnt(italic=True, color="CBD5E1", size=9)
    c.alignment = ctr()
    ws.merge_cells("A3:" + lc + "3")
    c = ws["A3"]
    c.value = ("  Orange background = REQUIRED    "
               "Green background = OPTIONAL    "
               "API Name must match exactly across all sheets")
    c.fill = fill("F1F5F9")
    c.font = fnt(italic=True, color="64748B", size=8)
    c.alignment = lft(wrap=False)


def build_sheet(wb, name, title, subtitle, bg, col_defs,
                tbl_name, tbl_style, hdr_row=4, data_row=5):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A" + str(data_row)
    banner(ws, title, subtitle, bg, len(col_defs))
    ws.row_dimensions[hdr_row].height = 50
    for ci, (h, w, req, dv_key, note) in enumerate(col_defs, 1):
        cl = get_column_letter(ci)
        ws.column_dimensions[cl].width = w
        c = ws.cell(hdr_row, ci, h)
        hdr_cell(c, bg)
        if note:
            c.comment = Comment(note, "COE Template")
        for r in range(data_row, data_row + ROWS):
            ws.row_dimensions[r].height = 18
            cell = ws.cell(r, ci)
            req_cell(cell) if req else opt_cell(cell)
        if dv_key and dv_key in REF:
            sqref = cl + str(data_row) + ":" + cl + str(data_row + ROWS - 1)
            add_dv(ws, REF[dv_key], sqref, h.rstrip(" *").split(": ")[-1])
    last_col = get_column_letter(len(col_defs))
    tbl = Table(displayName=tbl_name,
                ref="A" + str(hdr_row) + ":" + last_col + str(hdr_row + ROWS))
    tbl.tableStyleInfo = TableStyleInfo(name=tbl_style, showRowStripes=True)
    ws.add_table(tbl)
    return ws


def build(output_path):
    wb = Workbook()
    wb.remove(wb.active)

    # ── Instructions ──────────────────────────────────────────────────────────
    wi = wb.create_sheet("Instructions")
    wi.sheet_view.showGridLines = False
    wi.column_dimensions["A"].width = 30
    wi.column_dimensions["B"].width = 75
    wi.row_dimensions[1].height = 38
    wi.merge_cells("A1:B1")
    c = wi["A1"]
    c.value = "Integration COE - API Catalog Data Collection Template"
    c.fill = fill(C["navy"])
    c.font = fnt(bold=True, color="FFFFFF", size=15)
    c.alignment = lft(wrap=False)
    wi.row_dimensions[2].height = 18
    wi.merge_cells("A2:B2")
    c = wi["A2"]
    c.value = "MuleSoft 4.x to 4.9 Migration Programme  |  Complete all sheets and return to COE Lead"
    c.fill = fill(C["blue"])
    c.font = fnt(italic=True, color="CBD5E1", size=10)
    c.alignment = lft(wrap=False)

    inst = [
        (4,  "SHEET GUIDE", "", True),
        (5,  "1. APIs (Core)",
             "ONE ROW PER API. Orange = required. Green = optional. "
             "All other sheets join to this one by API Name.", False),
        (6,  "2. Dependencies",
             "ONE ROW PER RELATIONSHIP. An API with 3 consumers needs 3 rows. "
             "Direction column distinguishes consumer vs upstream.", False),
        (7,  "3. Policies & Libraries",
             "ONE ROW PER POLICY OR LIBRARY. "
             "Set Type column to Gateway Policy or Shared Library.", False),
        (8,  "4. Migration Plan",
             "ONE ROW PER API. Wave assignment, target dates, blocker details.", False),
        (9,  "5. CoE Metadata",
             "ONE ROW PER API. Security / Solution Design / Operations. "
             "All optional except API Name.", False),
        (10, "REF_DATA",
             "Reference lists for dropdowns. READ ONLY - password protected.", False),
        (12, "RULES", "", True),
        (13, "API Name is the join key",
             "Must be identical on every sheet - same spelling, same case, no extra spaces.", False),
        (14, "Multi-value fields",
             "Environments, Application Context, Compliance Flags: "
             "comma-separated in one cell.  Example: DEV, SIT, PROD", False),
        (15, "Dates",
             "Use YYYY-MM-DD format (e.g. 2026-06-30).", False),
        (16, "Do not add or remove columns",
             "Column order is fixed for the import script. "
             "Extra notes go in the Notes column.", False),
        (18, "HOW TO IMPORT", "", True),
        (19, "Step 1", "Fill all sheets. Save the workbook.", False),
        (20, "Step 2",
             "Export each data sheet as CSV: File -> Save a Copy -> CSV UTF-8 "
             "(repeat once per sheet).", False),
        (21, "Step 3",
             "Name the CSVs: apis.csv  dependencies.csv  "
             "policies-libs.csv  migration-plan.csv  coe-metadata.csv", False),
        (22, "Step 4",
             "Run: python3 excel-import.py --apis apis.csv --deps dependencies.csv "
             "--policies policies-libs.csv --migration migration-plan.csv "
             "--coe coe-metadata.csv", False),
        (23, "Step 5",
             "Load the produced api-data.json in index.html to view the catalog.", False),
    ]
    for row, label, value, is_hdr in inst:
        wi.row_dimensions[row].height = 20 if is_hdr else 36
        if is_hdr:
            wi.merge_cells("A" + str(row) + ":B" + str(row))
            c = wi.cell(row, 1, "  " + label)
            c.fill = fill(C["blue"])
            c.font = fnt(bold=True, color="FFFFFF", size=10)
            c.alignment = lft(wrap=False)
        else:
            lc = wi.cell(row, 1, label)
            lc.font = fnt(bold=True, color=C["blue"], size=10)
            lc.fill = fill("F8FAFC")
            lc.alignment = lft(wrap=False)
            vc = wi.cell(row, 2, value)
            vc.font = fnt(color="334155", size=10)
            vc.fill = fill("F8FAFC")
            vc.alignment = lft(wrap=True)

    # ── Sheet 1: APIs Core ────────────────────────────────────────────────────
    build_sheet(wb, "1_APIs_Core",
        "1. APIs - Core Fields",
        "One row per API  |  Orange = Required  |  Green = Optional",
        C["hdr_api"], [
        ("API Name *",            28, True,  None,            "KEY FIELD - must match exactly on all other sheets"),
        ("Repo / Exchange Name",  28, False, None,            "Anypoint Exchange or Git asset name"),
        ("Version",               12, True,  None,            "e.g. 1.2.0"),
        ("Layer *",               14, True,  "layers",        "EAPI / PAPI / SAPI / BATCH / EVENT / UTILITY / FACADE"),
        ("Protocol",              14, False, "protocols",     "REST / SOAP / Kafka etc."),
        ("Runtime Version *",     20, True,  "runtimes",      "Select Mule runtime version from list"),
        ("Runtime Type 1",        24, False, "runtime_types", "Primary topology type"),
        ("Runtime Type 2",        24, False, "runtime_types", "Second topology type if applicable"),
        ("Java Version",          14, False, "java",          "Java 8 / 11 / 17"),
        ("Deployment Model",      18, False, "deploy",        "OnPrem / AWS / Hybrid / CloudHub"),
        ("Environments",          26, True,  None,            "Comma-separated: DEV, SIT, UAT, PROD"),
        ("Tribe *",               26, True,  "tribes",        "Owning tribe"),
        ("Squad *",               24, True,  None,            "Squad name within the tribe"),
        ("Application Context",   30, False, None,            "Comma-separated - apps this API serves"),
        ("Business Domain (L0)",  24, False, None,            "e.g. Payments, Customer, Cards"),
        ("Capability (L1)",       24, False, None,            "e.g. Payment Processing, Identity"),
        ("Sub-Capability (L2)",   24, False, None,            "e.g. Card Tokenisation"),
        ("Status *",              14, True,  "status",        "Active / Deprecated / Inactive / Review"),
        ("Migration Status *",    20, True,  "mig_status",    "Current migration state"),
        ("Migration Complexity",  20, False, "complexity",    "Low / Medium / High"),
        ("Tags",                  28, False, None,            "Comma-separated free-form tags"),
        ("Notes",                 40, False, None,            "Additional context"),
    ], "tbl_APIs", "TableStyleMedium2")

    # ── Sheet 2: Dependencies ─────────────────────────────────────────────────
    build_sheet(wb, "2_Dependencies",
        "2. Consumers & Upstream Dependencies",
        "One row per relationship  |  Direction distinguishes consumer vs upstream",
        C["hdr_dep"], [
        ("API Name *",               28, True,  None,        "Must exactly match API Name in sheet 1"),
        ("Direction *",              32, True,  "dep_dir",   "Consumer = calls this API | Upstream = this API calls it"),
        ("System / API Name *",      30, True,  None,        "Use exact catalog API name if internal"),
        ("Environments",             24, False, None,        "Comma-separated: DEV, SIT, PROD"),
        ("Contract Type / Protocol", 20, False, "protocols", "REST / SOAP / Kafka etc."),
        ("Notes",                    50, False, None,        "Latency, idempotency requirements etc."),
        ("External System?",         16, False, "yes_no",    "Yes if outside the Mule catalog"),
        ("External System Name",     28, False, None,        "Full name if external - used in dependency graph"),
    ], "tbl_Deps", "TableStyleMedium4")

    # ── Sheet 3: Policies & Libraries ─────────────────────────────────────────
    ws3 = build_sheet(wb, "3_Policies_Libraries",
        "3. Gateway Policies & Shared Libraries",
        "One row per policy or library  |  Type column distinguishes them",
        C["hdr_gw"], [
        ("API Name *",   28, True,  None,       "Must match sheet 1"),
        ("Type *",       22, True,  None,       "Gateway Policy  or  Shared Library"),
        ("Name *",       30, True,  None,       "Policy or library name"),
        ("Version",      14, False, None,       "e.g. 1.3.0"),
        ("Scope",        28, False, "pol_scope","API Manager / Kafka / Exchange"),
        ("Group ID",     32, False, None,       "Maven groupId for shared libraries"),
        ("Exchange URL", 44, False, None,       "Anypoint Exchange URL"),
        ("Notes",        50, False, None,       "Audit requirements, caveats"),
    ], "tbl_Policies", "TableStyleMedium6")
    type_dv = DataValidation(
        type="list", formula1='"Gateway Policy,Shared Library"',
        allow_blank=True, showDropDown=False,
        showErrorMessage=True, errorTitle="Invalid",
        error="Type must be Gateway Policy or Shared Library")
    ws3.add_data_validation(type_dv)
    type_dv.sqref = "B5:B" + str(4 + ROWS)

    # ── Sheet 4: Migration Plan ───────────────────────────────────────────────
    build_sheet(wb, "4_Migration_Plan",
        "4. Migration Plan",
        "One row per API  |  Wave + dates + blocker details",
        C["hdr_mig"], [
        ("API Name *",             28, True,  None,        "Must match sheet 1"),
        ("Wave Assignment *",      18, True,  "waves",     "Wave 1 / Wave 2 / Wave 3 / Unassigned"),
        ("Target Start Date",      18, False, None,        "YYYY-MM-DD"),
        ("Target End Date",        18, False, None,        "YYYY-MM-DD"),
        ("Actual Completion Date", 20, False, None,        "YYYY-MM-DD - fill when done"),
        ("Migration Status *",     20, True,  "mig_status","Current status"),
        ("Blocker Reason",         50, False, None,        "Required if Blocked - what prevents migration"),
        ("Blocker Owner",          28, False, None,        "Email or team responsible"),
        ("Notes",                  40, False, None,        "Other migration context"),
    ], "tbl_Migration", "TableStyleMedium7")

    # ── Sheet 5: CoE Metadata ─────────────────────────────────────────────────
    ws5 = wb.create_sheet("5_CoE_Metadata")
    ws5.sheet_view.showGridLines = False
    coe_cols = [
        ("API Name *",                 28, True,  None,         "Must match sheet 1"),
        ("SEC: Auth Scheme",           22, False, "auth",       None),
        ("SEC: OAuth Scopes",          26, False, None,         "Comma-separated scopes"),
        ("SEC: TLS Version",           14, False, "tls",        None),
        ("SEC: Data Classification",   18, False, "data_class", None),
        ("SEC: Compliance Flags",      24, False, None,         "Comma-separated: PCI-DSS, GDPR, SOX"),
        ("SEC: Secrets Vault Path",    28, False, None,         None),
        ("SEC: Cert Expiry Date",      16, False, None,         "YYYY-MM-DD - drives red/amber alerts in viewer"),
        ("SEC: Known Vulnerabilities", 40, False, None,         None),
        ("SD: Architectural Pattern",  24, False, None,         "Orchestration / Proxy / Event-driven / Facade"),
        ("SD: Versioning Strategy",    22, False, None,         None),
        ("SD: Error Handling",         28, False, None,         None),
        ("SD: SLA Target",             16, False, None,         "e.g. 99.9%"),
        ("SD: ADR Links",              40, False, None,         "Comma-separated URLs"),
        ("SD: Technical Debt",         50, False, None,         None),
        ("SD: Domain Events",          40, False, None,         "Comma-separated"),
        ("OPS: On-Call Contact",       24, False, None,         "Email or team name"),
        ("OPS: Uptime SLA",            14, False, None,         None),
        ("OPS: Alerting Threshold",    28, False, None,         "e.g. Error rate > 2% over 5 min"),
        ("OPS: Maintenance Window",    24, False, None,         None),
        ("OPS: Runbook Links",         40, False, None,         "Comma-separated URLs"),
        ("OPS: Monitoring Links",      40, False, None,         "Comma-separated URLs"),
        ("OPS: Known Fragilities",     50, False, None,         None),
        ("OPS: Pipeline Link",         40, False, None,         None),
    ]
    nc = len(coe_cols)
    lc = get_column_letter(nc)
    banner(ws5,
           "5. CoE Metadata - Security / Solution Design / Operations",
           "One row per API  |  Fill what you know  |  Owned by respective CoE leads",
           C["hdr_coe"], nc)

    ws5.row_dimensions[4].height = 18
    for lbl, c1, c2, bg in [
        ("IDENTITY",             1,  1,  C["hdr_coe"]),
        ("SECURITY COE",         2,  9,  "1E3A5F"),
        ("SOLUTION DESIGN COE", 10, 16,  "312E81"),
        ("OPERATIONS COE",      17, 24,  "14532D"),
    ]:
        ws5.merge_cells(start_row=4, start_column=c1, end_row=4, end_column=c2)
        c = ws5.cell(4, c1, lbl)
        c.fill = fill(bg)
        c.font = fnt(bold=True, color="FFFFFF", size=9)
        c.alignment = ctr()

    ws5.row_dimensions[5].height = 50
    ws5.freeze_panes = "A6"

    def coe_bg(ci):
        if ci == 1:        return C["hdr_coe"]
        if 2 <= ci <= 9:   return "1E3A5F"
        if 10 <= ci <= 16: return "312E81"
        return "14532D"

    for ci, (h, w, req, dv_key, note) in enumerate(coe_cols, 1):
        cl = get_column_letter(ci)
        ws5.column_dimensions[cl].width = w
        c = ws5.cell(5, ci, h)
        hdr_cell(c, coe_bg(ci))
        if note:
            c.comment = Comment(note, "COE Template")
        for r in range(6, 6 + ROWS):
            ws5.row_dimensions[r].height = 18
            cell = ws5.cell(r, ci)
            req_cell(cell) if req else opt_cell(cell)
        if dv_key and dv_key in REF:
            sqref = cl + "6:" + cl + str(5 + ROWS)
            add_dv(ws5, REF[dv_key], sqref, h.split(": ")[-1])

    t5 = Table(displayName="tbl_CoE",
               ref="A5:" + lc + str(5 + ROWS))
    t5.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9",
                                       showRowStripes=True)
    ws5.add_table(t5)

    # ── REF_DATA ──────────────────────────────────────────────────────────────
    wr = wb.create_sheet("REF_DATA")
    wr.sheet_view.showGridLines = False
    wr.sheet_properties.tabColor = "6B7280"
    wr.row_dimensions[1].height = 26
    wr.merge_cells("A1:P1")
    c = wr["A1"]
    c.value = "  Reference Data - DO NOT EDIT  |  Drives all dropdowns across the workbook"
    c.fill = fill("374151")
    c.font = fnt(bold=True, color="FFFFFF", size=11)
    c.alignment = lft(wrap=False)

    ref_sections = [
        ("Layers",              REF["layers"]),
        ("Protocols",           REF["protocols"]),
        ("Runtime Versions",    REF["runtimes"]),
        ("Runtime Types",       REF["runtime_types"]),
        ("Java Versions",       REF["java"]),
        ("Deployment Models",   REF["deploy"]),
        ("API Status",          REF["status"]),
        ("Migration Status",    REF["mig_status"]),
        ("Complexity",          REF["complexity"]),
        ("Waves",               REF["waves"]),
        ("Auth Schemes",        REF["auth"]),
        ("TLS Versions",        REF["tls"]),
        ("Data Classification", REF["data_class"]),
        ("Tribes",              REF["tribes"]),
        ("Dep Direction",       REF["dep_dir"]),
        ("Policy Scope",        REF["pol_scope"]),
    ]
    for col_i, (section_name, values) in enumerate(ref_sections, 1):
        wr.column_dimensions[get_column_letter(col_i)].width = 26
        h = wr.cell(2, col_i, section_name)
        h.fill = fill(C["blue"])
        h.font = fnt(bold=True, color="FFFFFF", size=9)
        h.alignment = ctr()
        h.border = bdr("334155")
        for row_i, val in enumerate(values, 3):
            c = wr.cell(row_i, col_i, val)
            c.fill = fill("F8FAFC" if row_i % 2 == 0 else "FFFFFF")
            c.font = fnt(color="1E293B", size=9)
            c.alignment = lft(wrap=False)
            c.border = bdr("E2E8F0")

    wr.protection.sheet = True
    wr.protection.password = "coe2026"

    wb.save(output_path)
    print(f"Saved: {output_path}")
    print(f"Sheets: {wb.sheetnames}")
    print(f"Data rows per sheet: {ROWS}")
    print()
    print("To update tribe names or runtime versions:")
    print("  Edit the REF dict in this script and re-run.")
    print("  Then update the matching arrays in api-data.json.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build Integration COE API Catalog Excel template"
    )
    parser.add_argument(
        "--output", default="api-catalog-template.xlsx",
        help="Output file path (default: api-catalog-template.xlsx)"
    )
    args = parser.parse_args()
    build(args.output)
