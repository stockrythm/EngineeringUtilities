#!/usr/bin/env python3
"""
excel-import.py — Integration COE API Catalog
==============================================
Reads the five CSV exports from api-catalog-template.xlsx and
produces a valid api-data.json ready to load in the catalog.

Usage
-----
  # Full import (all 5 sheets)
  python3 excel-import.py \\
    --apis           apis.csv \\
    --deps           dependencies.csv \\
    --policies       policies-libs.csv \\
    --migration      migration-plan.csv \\
    --coe            coe-metadata.csv

  # Partial import — any sheet can be omitted
  python3 excel-import.py --apis apis.csv --migration migration-plan.csv

  # Merge into existing catalog (preserves already-enriched APIs)
  python3 excel-import.py --apis apis.csv --deps dependencies.csv \\
    --merge existing-api-data.json

  # Interactive mode
  python3 excel-import.py

Joining key
-----------
  "API Name" column on every sheet joins to api.name.
  Matching is case-insensitive and whitespace-normalised.
  A warning is emitted for every row whose API Name does not
  match anything in the APIs sheet.
"""

import csv, json, os, re, sys, argparse
from datetime import datetime

# ── Helpers ───────────────────────────────────────────────────────────────────

def norm(s):
    """Normalise a string for comparison: lower + collapse whitespace."""
    return re.sub(r'\s+', ' ', (s or '').strip().lower())

def clean(s):
    """Strip whitespace from a raw cell value."""
    return (s or '').strip()

def split_csv_field(s, sep=','):
    """Split a comma-separated cell into a cleaned list, drop blanks."""
    return [x.strip() for x in (s or '').split(sep) if x.strip()]

def is_yes(s):
    return norm(s) in {'yes', 'y', 'true', '1', 'x', '✓'}

def make_id():
    now = datetime.now()
    return (f"api-{now.year}"
            f"{str(now.month).zfill(2)}{str(now.day).zfill(2)}"
            f"{str(now.hour).zfill(2)}{str(now.minute).zfill(2)}"
            f"{str(now.second).zfill(2)}"
            f"{str(now.microsecond)[:3]}")

def norm_runtime(s):
    if not s: return ''
    if re.match(r'^MuleSoft \d', s): return s
    m = re.search(r'(\d+\.\d+(?:\.\d+)?)', s)
    return f"MuleSoft {m.group(1)}" if m else s

def infer_java(runtime):
    m = re.search(r'(\d+)\.(\d+)', runtime or '')
    if not m: return ''
    major, minor = int(m.group(1)), int(m.group(2))
    if major == 3: return 'Java 8'
    if major == 4 and minor <= 6: return 'Java 8'
    if major == 4 and minor >= 7: return 'Java 17'
    return ''

def norm_status(s):
    MAP = {'active':'Active','live':'Active','production':'Active',
           'deprecated':'Deprecated','retired':'Deprecated','decommissioned':'Deprecated',
           'inactive':'Inactive','disabled':'Inactive',
           'review':'Review','draft':'Review'}
    return MAP.get(norm(s), 'Active')

def norm_mig_status(s):
    MAP = {'not started':'Not Started','notstarted':'Not Started',
           'in analysis':'In Analysis','analysis':'In Analysis',
           'in progress':'In Progress','inprogress':'In Progress',
           'blocked':'Blocked',
           'complete':'Complete','completed':'Complete','done':'Complete',
           'decommission candidate':'Decommission Candidate',
           'decommission':'Decommission Candidate'}
    return MAP.get(norm(s), 'Not Started')

def norm_wave(s):
    n = norm(s)
    if 'wave 1' in n or 'wave1' in n: return 'wave-1'
    if 'wave 2' in n or 'wave2' in n: return 'wave-2'
    if 'wave 3' in n or 'wave3' in n: return 'wave-3'
    return 'unassigned'

def read_csv(path):
    """Read CSV, return (headers_norm, rows_as_lists)."""
    if not path or not os.path.exists(path):
        return [], []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return [], []
    headers = [norm(h) for h in rows[0]]
    return headers, rows[1:]

def col(headers, row, *names):
    """Get first matching column value by header name variants."""
    for name in names:
        n = norm(name)
        try:
            i = headers.index(n)
            return clean(row[i]) if i < len(row) else ''
        except ValueError:
            pass
    return ''

def empty_api():
    return {
        "id":               "",
        "name":             "",
        "repoApiName":      "",
        "version":          "",
        "layer":            "",
        "protocol":         "REST",
        "runtime":          "",
        "runtimeType":      [],
        "javaVersion":      "",
        "deploymentModel":  "",
        "environments":     [],
        "tribeId":          "",
        "owningSquad":      "",
        "applicationContext": [],
        "businessCapability": {"l0": "", "l1": "", "l2": ""},
        "consumers":        [],
        "upstreamSystems":  [],
        "status":           "Active",
        "migrationStatus":  "Not Started",
        "migrationComplexity": "Medium",
        "ramlSpec":         "",
        "confluenceLinks":  [],
        "designReferences": [],
        "operationalNotes": [],
        "tags":             [],
        "lastReviewedBy":   "",
        "lastReviewedDate": "",
        "security": {
            "authScheme": "", "oauthScopes": [], "tlsVersion": "",
            "gatewayPolicies": [], "dataClassification": "",
            "complianceFlags": [], "secretsVaultPath": "",
            "certExpiry": "", "knownVulnerabilities": []
        },
        "solutionDesign": {
            "architecturalPattern": "", "versioningStrategy": "",
            "errorHandlingStrategy": "", "slaTarget": "",
            "asyncApiSpec": "", "adrLinks": [],
            "technicalDebt": [], "domainEvents": []
        },
        "operations": {
            "oncallContact": "", "monitoringLinks": [],
            "alertingThreshold": "", "maintenanceWindow": "",
            "runbookLinks": [], "incidentRefs": [],
            "knownFragilities": [], "pipelineLink": "", "uptimeSla": ""
        },
        "dependencies": {
            "gatewayPolicies": [],
            "sharedLibraries": []
        },
        "migrationPlan": {
            "wave": "unassigned", "targetStartDate": "",
            "targetDate": "", "completionDate": "",
            "blockerReason": "", "blockerOwner": ""
        }
    }

def tribe_id_from_name(name):
    """Best-effort tribe name → id mapping."""
    MAP = {
        'payments':                   'tribe-pmt',
        'customer':                   'tribe-cust',
        'cards':                      'tribe-cards',
        'commercial digital channel': 'tribe-cdc',
        'retail digital channel':     'tribe-rdc',
        'homebuying':                 'tribe-hb',
    }
    return MAP.get(norm(name), '')

# ── Sheet parsers ──────────────────────────────────────────────────────────────

def parse_apis(path, existing_ids):
    headers, rows = read_csv(path)
    if not headers:
        return {}, []
    apis_by_norm_name = {}
    warnings = []
    for row_num, row in enumerate(rows, 2):
        name = col(headers, row, 'api name *', 'api name', 'name')
        if not name:
            warnings.append(f'Row {row_num}: no API Name — skipped')
            continue
        api = empty_api()
        api['id']            = make_id()
        while api['id'] in existing_ids:
            import time; time.sleep(0.001); api['id'] = make_id()
        existing_ids.add(api['id'])
        api['name']          = name
        api['repoApiName']   = col(headers, row, 'repo / exchange name', 'repo name', 'exchange name', 'repoApiName') or name
        api['version']       = col(headers, row, 'version')
        api['layer']         = col(headers, row, 'layer *', 'layer', 'type')
        api['protocol']      = col(headers, row, 'protocol') or 'REST'
        rt = norm_runtime(col(headers, row, 'runtime version *', 'runtime version', 'runtime'))
        api['runtime']       = rt
        api['javaVersion']   = col(headers, row, 'java version') or infer_java(rt)
        api['deploymentModel'] = col(headers, row, 'deployment model')

        # Runtime types — up to 2 columns
        rt1 = col(headers, row, 'runtime type 1', 'runtime type')
        rt2 = col(headers, row, 'runtime type 2')
        api['runtimeType']   = [x for x in [rt1, rt2] if x]

        api['environments']  = split_csv_field(col(headers, row, 'environments'))
        tribe_name           = col(headers, row, 'tribe *', 'tribe')
        api['tribeId']       = tribe_id_from_name(tribe_name)
        if tribe_name and not api['tribeId']:
            warnings.append(f'Row {row_num}: "{name}" — tribe "{tribe_name}" not recognised, tribeId left blank')
        api['owningSquad']   = col(headers, row, 'squad *', 'squad', 'owning squad')
        api['applicationContext'] = split_csv_field(col(headers, row, 'application context'))
        api['businessCapability']['l0'] = col(headers, row, 'business domain (l0)', 'l0')
        api['businessCapability']['l1'] = col(headers, row, 'capability (l1)', 'l1')
        api['businessCapability']['l2'] = col(headers, row, 'sub-capability (l2)', 'l2')
        api['status']        = norm_status(col(headers, row, 'status *', 'status'))
        api['migrationStatus'] = norm_mig_status(col(headers, row, 'migration status *', 'migration status'))
        cx = col(headers, row, 'migration complexity', 'complexity')
        api['migrationComplexity'] = cx if cx in ('Low','Medium','High') else 'Medium'
        api['tags']          = split_csv_field(col(headers, row, 'tags'))
        notes = col(headers, row, 'notes')
        if notes: api['operationalNotes'].append(notes)
        apis_by_norm_name[norm(name)] = api
    return apis_by_norm_name, warnings


def parse_dependencies(path, apis_map):
    headers, rows = read_csv(path)
    warnings = []
    if not headers:
        return warnings
    for row_num, row in enumerate(rows, 2):
        api_name = col(headers, row, 'api name *', 'api name')
        api = apis_map.get(norm(api_name))
        if not api:
            warnings.append(f'Row {row_num}: Deps — API "{api_name}" not found in APIs sheet')
            continue
        direction = col(headers, row, 'direction *', 'direction')
        system    = col(headers, row, 'system / api name *', 'system / api name', 'system')
        envs      = split_csv_field(col(headers, row, 'environments'))
        contract  = col(headers, row, 'contract type / protocol', 'contract type', 'protocol')
        notes     = col(headers, row, 'notes')

        if not system:
            warnings.append(f'Row {row_num}: Deps — no system name, skipped')
            continue

        is_consumer = 'consumer' in norm(direction)
        entry = {
            'system':       system,
            'environments': envs,
            'notes':        notes
        }
        if is_consumer:
            entry['contractType'] = contract
            api['consumers'].append(entry)
        else:
            entry['protocol'] = contract
            api['upstreamSystems'].append(entry)
    return warnings


def parse_policies(path, apis_map):
    headers, rows = read_csv(path)
    warnings = []
    if not headers:
        return warnings
    for row_num, row in enumerate(rows, 2):
        api_name = col(headers, row, 'api name *', 'api name')
        api = apis_map.get(norm(api_name))
        if not api:
            warnings.append(f'Row {row_num}: Policies — API "{api_name}" not found in APIs sheet')
            continue
        entry_type = norm(col(headers, row, 'type *', 'type'))
        name       = col(headers, row, 'name *', 'name')
        version    = col(headers, row, 'version')
        scope      = col(headers, row, 'scope')
        group_id   = col(headers, row, 'group id', 'groupid', 'group_id')
        exch_url   = col(headers, row, 'exchange url', 'exchangeurl')
        notes      = col(headers, row, 'notes')

        if not name:
            warnings.append(f'Row {row_num}: Policies — no name, skipped')
            continue

        if 'library' in entry_type or 'shared' in entry_type:
            api['dependencies']['sharedLibraries'].append({
                'name': name, 'groupId': group_id,
                'version': version, 'scope': scope or 'POM dependency',
                'exchangeUrl': exch_url
            })
        else:
            api['dependencies']['gatewayPolicies'].append({
                'name': name, 'version': version,
                'scope': scope or 'API Manager', 'notes': notes
            })
    return warnings


def parse_migration(path, apis_map):
    headers, rows = read_csv(path)
    warnings = []
    if not headers:
        return warnings
    for row_num, row in enumerate(rows, 2):
        api_name = col(headers, row, 'api name *', 'api name')
        api = apis_map.get(norm(api_name))
        if not api:
            warnings.append(f'Row {row_num}: Migration — API "{api_name}" not found in APIs sheet')
            continue
        api['migrationPlan'] = {
            'wave':            norm_wave(col(headers, row, 'wave assignment *', 'wave assignment', 'wave')),
            'targetStartDate': col(headers, row, 'target start date', 'start date'),
            'targetDate':      col(headers, row, 'target end date', 'target date', 'end date'),
            'completionDate':  col(headers, row, 'actual completion date', 'completion date'),
            'blockerReason':   col(headers, row, 'blocker reason'),
            'blockerOwner':    col(headers, row, 'blocker owner'),
        }
        # Override migration status from this sheet if provided
        ms = col(headers, row, 'migration status *', 'migration status')
        if ms: api['migrationStatus'] = norm_mig_status(ms)
    return warnings


def parse_coe(path, apis_map):
    headers, rows = read_csv(path)
    warnings = []
    if not headers:
        return warnings
    for row_num, row in enumerate(rows, 2):
        api_name = col(headers, row, 'api name *', 'api name')
        api = apis_map.get(norm(api_name))
        if not api:
            warnings.append(f'Row {row_num}: CoE — API "{api_name}" not found in APIs sheet')
            continue
        s = api['security']
        s['authScheme']         = col(headers, row, 'sec: auth scheme', 'auth scheme')
        s['oauthScopes']        = split_csv_field(col(headers, row, 'sec: oauth scopes', 'oauth scopes'))
        s['tlsVersion']         = col(headers, row, 'sec: tls version', 'tls version')
        s['dataClassification'] = col(headers, row, 'sec: data classification', 'data classification')
        s['complianceFlags']    = split_csv_field(col(headers, row, 'sec: compliance flags', 'compliance flags'))
        s['secretsVaultPath']   = col(headers, row, 'sec: secrets vault path', 'vault path')
        s['certExpiry']         = col(headers, row, 'sec: cert expiry date', 'cert expiry')
        vuln = col(headers, row, 'sec: known vulnerabilities', 'known vulnerabilities')
        if vuln: s['knownVulnerabilities'] = [vuln]

        d = api['solutionDesign']
        d['architecturalPattern']  = col(headers, row, 'sd: architectural pattern', 'architectural pattern')
        d['versioningStrategy']    = col(headers, row, 'sd: versioning strategy', 'versioning strategy')
        d['errorHandlingStrategy'] = col(headers, row, 'sd: error handling', 'error handling')
        d['slaTarget']             = col(headers, row, 'sd: sla target', 'sla target')
        adr = col(headers, row, 'sd: adr links', 'adr links')
        if adr: d['adrLinks'] = [{'label': u.strip(), 'url': u.strip()} for u in adr.split(',') if u.strip()]
        debt = col(headers, row, 'sd: technical debt', 'technical debt')
        if debt: d['technicalDebt'] = [debt]
        events = col(headers, row, 'sd: domain events', 'domain events')
        if events: d['domainEvents'] = split_csv_field(events)

        o = api['operations']
        o['oncallContact']     = col(headers, row, 'ops: on-call contact', 'on-call contact', 'oncall contact')
        o['uptimeSla']         = col(headers, row, 'ops: uptime sla', 'uptime sla')
        o['alertingThreshold'] = col(headers, row, 'ops: alerting threshold', 'alerting threshold')
        o['maintenanceWindow'] = col(headers, row, 'ops: maintenance window', 'maintenance window')
        runbooks = col(headers, row, 'ops: runbook links', 'runbook links')
        if runbooks:
            o['runbookLinks'] = [{'label': u.strip(), 'url': u.strip()} for u in runbooks.split(',') if u.strip()]
        monitoring = col(headers, row, 'ops: monitoring links', 'monitoring links')
        if monitoring:
            o['monitoringLinks'] = [{'label': u.strip(), 'url': u.strip()} for u in monitoring.split(',') if u.strip()]
        frags = col(headers, row, 'ops: known fragilities', 'known fragilities')
        if frags: o['knownFragilities'] = [frags]
        o['pipelineLink'] = col(headers, row, 'ops: pipeline link', 'pipeline link')
    return warnings


# ── Main ──────────────────────────────────────────────────────────────────────

def run(paths, merge_path=None, output_path='api-data.json'):
    existing_catalog = None
    existing_ids     = set()
    existing_by_name = {}

    if merge_path and os.path.exists(merge_path):
        with open(merge_path) as f:
            existing_catalog = json.load(f)
        existing_ids = {a['id'] for a in existing_catalog.get('apis', [])}
        existing_by_name = {norm(a['name']): a for a in existing_catalog.get('apis', [])}
        print(f'Merge mode: {len(existing_by_name)} existing APIs loaded from {merge_path}')

    all_warnings = []

    # Parse APIs sheet first — builds the keyed dict
    apis_map, w = parse_apis(paths.get('apis'), existing_ids)
    all_warnings += [('APIs', x) for x in w]

    # Merge check: skip APIs already in existing catalog
    duplicates = []
    if existing_catalog:
        for nm in list(apis_map.keys()):
            if nm in existing_by_name:
                duplicates.append(apis_map[nm]['name'])
                del apis_map[nm]

    # Parse remaining sheets — all enrich entries in apis_map
    for sheet, parser in [
        ('deps',      lambda: parse_dependencies(paths.get('deps'), apis_map)),
        ('policies',  lambda: parse_policies(paths.get('policies'), apis_map)),
        ('migration', lambda: parse_migration(paths.get('migration'), apis_map)),
        ('coe',       lambda: parse_coe(paths.get('coe'), apis_map)),
    ]:
        w = parser()
        all_warnings += [(sheet, x) for x in w]

    # Build final catalog
    new_apis = list(apis_map.values())
    if existing_catalog:
        catalog = existing_catalog
        catalog['apis'].extend(new_apis)
        catalog['meta']['lastUpdated'] = datetime.now().strftime('%Y-%m-%d')
    else:
        catalog = {
            'meta': {
                'version':      '1.6.0',
                'lastUpdated':  datetime.now().strftime('%Y-%m-%d'),
                'organization': '',
                'catalogOwner': ''
            },
            'layerSuggestions':  ['EAPI','PAPI','SAPI','BATCH','EVENT','UTILITY','FACADE'],
            'contractTypes':     ['REST','SOAP','Kafka','AsyncAPI','GraphQL','SFTP','JMS','Other'],
            'runtimeVersions':   ['MuleSoft 4.1','MuleSoft 4.2','MuleSoft 4.3',
                                  'MuleSoft 4.4','MuleSoft 4.5','MuleSoft 4.6',
                                  'MuleSoft 4.7','MuleSoft 4.8','MuleSoft 4.9',
                                  'MuleSoft 3.9 (Legacy)'],
            'runtimeTypes':      ['AWS Egress Runtime','AWS Ingress Runtime',
                                  'IGZ Egress','IGZ Ingress','Qsystem',
                                  'Process','Experience','System'],
            'deploymentModels':  ['OnPrem','AWS','Azure','Hybrid','CloudHub'],
            'javaVersions':      ['Java 8','Java 11','Java 17','Java 21'],
            'tribes': [
                {'id':'tribe-pmt',   'name':'Payments',                   'lead':''},
                {'id':'tribe-cust',  'name':'Customer',                   'lead':''},
                {'id':'tribe-cards', 'name':'Cards',                      'lead':''},
                {'id':'tribe-cdc',   'name':'Commercial Digital Channel', 'lead':''},
                {'id':'tribe-rdc',   'name':'Retail Digital Channel',     'lead':''},
                {'id':'tribe-hb',    'name':'Homebuying',                 'lead':''},
            ],
            'businessCapabilities': [],
            'migrationWaves': [
                {'id':'wave-1','name':'Wave 1','description':'Foundation & Platform APIs',
                 'startDate':'','endDate':'','color':'#6366f1'},
                {'id':'wave-2','name':'Wave 2','description':'Core Business APIs',
                 'startDate':'','endDate':'','color':'#3b82f6'},
                {'id':'wave-3','name':'Wave 3','description':'Experience & Channel APIs',
                 'startDate':'','endDate':'','color':'#22d3ee'},
                {'id':'unassigned','name':'Unassigned','description':'',
                 'startDate':'','endDate':'','color':'#64748b'},
            ],
            'apis': new_apis
        }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    # ── Report ────────────────────────────────────────────────────────────────
    report_path = output_path.replace('.json', '-import-report.txt')
    lines = [
        '═' * 64,
        '  Integration COE — Excel Import Report',
        f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        '═' * 64, '',
        f'  Mode        : {"Merge into " + merge_path if merge_path else "Fresh import"}',
        f'  Output JSON : {output_path}', '',
        '─' * 64,
        '  IMPORT SUMMARY',
        '─' * 64,
        f'  ✅ APIs imported     : {len(new_apis)}',
        f'  🔁 Duplicates skipped: {len(duplicates)} (already in catalog)',
        f'  ⚠  Warnings          : {len(all_warnings)}', '',
    ]

    if duplicates:
        lines += ['─'*64, '  DUPLICATES (not imported — already exist)', '─'*64]
        for n in duplicates: lines.append(f'  • {n}')
        lines.append('')

    if all_warnings:
        lines += ['─'*64, '  WARNINGS', '─'*64]
        for sheet, msg in all_warnings:
            lines.append(f'  [{sheet.upper():<10}] {msg}')
        lines.append('')

    lines += [
        '─' * 64,
        '  ENRICHMENT CHECKLIST — work through these in editor.html',
        '─' * 64,
        '  Priority  Field                  Notes',
        '  ────────  ─────────────────────  ──────────────────────────────────',
        '  1 HIGH    tribeId                Required for all dependency maps',
        '  2 HIGH    consumers[]            Who calls each API',
        '  3 HIGH    upstreamSystems[]      What each API calls',
        '  4 HIGH    migrationPlan.wave     Assign to Wave 1/2/3',
        '  5 MED     layer                  Verify EAPI/PAPI/SAPI if blank',
        '  6 MED     applicationContext     Which apps does this API serve',
        '  7 MED     deploymentModel        OnPrem / AWS / Hybrid',
        '  8 MED     javaVersion            Confirm if auto-inference wrong',
        '  9 LOW     CoE sections           Security / SolutionDesign / Ops',
        ' 10 LOW     certExpiry             Drives red/amber alerts in viewer',
        '',
        '═' * 64,
    ]

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # Console summary
    print()
    print('═' * 64)
    print(f'  ✅  Imported  : {len(new_apis)} APIs')
    if duplicates:
        print(f'  🔁  Skipped   : {len(duplicates)} duplicates')
    if all_warnings:
        print(f'  ⚠   Warnings  : {len(all_warnings)} — see report')
    print(f'\n  Output JSON  → {output_path}')
    print(f'  Report       → {report_path}')
    print('═' * 64)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Import Excel template CSVs into api-data.json'
    )
    parser.add_argument('--apis',       help='Path to 1_APIs_Core.csv')
    parser.add_argument('--deps',       help='Path to 2_Dependencies.csv')
    parser.add_argument('--policies',   help='Path to 3_Policies_Libraries.csv')
    parser.add_argument('--migration',  help='Path to 4_Migration_Plan.csv')
    parser.add_argument('--coe',        help='Path to 5_CoE_Metadata.csv')
    parser.add_argument('--merge',      help='Merge into existing api-data.json')
    parser.add_argument('--output',     default='api-data.json')
    args = parser.parse_args()

    paths = {
        'apis':       args.apis,
        'deps':       args.deps,
        'policies':   args.policies,
        'migration':  args.migration,
        'coe':        args.coe,
    }

    # Interactive mode if nothing provided
    if not any(paths.values()):
        print('\nIntegration COE — Excel Import Tool')
        print('─' * 40)
        print('Press Enter to skip any sheet\n')
        paths['apis']      = input('  1_APIs_Core CSV path      : ').strip().strip('"')
        paths['deps']      = input('  2_Dependencies CSV path   : ').strip().strip('"')
        paths['policies']  = input('  3_Policies_Libs CSV path  : ').strip().strip('"')
        paths['migration'] = input('  4_Migration_Plan CSV path : ').strip().strip('"')
        paths['coe']       = input('  5_CoE_Metadata CSV path   : ').strip().strip('"')
        merge = input('  Merge into existing JSON? [y/N]: ').strip().lower()
        args.merge = input('  Existing JSON path: ').strip().strip('"') if merge == 'y' else None
        args.output = input('  Output path [api-data.json]: ').strip() or 'api-data.json'

    if not paths.get('apis') or not os.path.exists(paths['apis']):
        print('ERROR: --apis is required and must point to a valid CSV file')
        sys.exit(1)

    run(paths, merge_path=args.merge, output_path=args.output)
