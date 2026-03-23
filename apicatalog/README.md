# API Catalog

- `docs\api-catalog-template.xlsx` — the workbook your BA fills in. Open it directly in Excel. Six sheets: Instructions, APIs Core, Dependencies, Policies & Libraries, Migration Plan, CoE Metadata, and a password-protected `REF_DATA` sheet driving all the dropdowns. Orange cells are required, green are optional.


- `build_template.py` — run this on your laptop whenever you need to regenerate the template, for example after adding new tribes or runtime versions. Just edit the REF dict at the top of the script and run python3 build_template.py. Requires `pip install openpyxl`.

- `excel-import.py` — run this after your BA exports each sheet as CSV. Takes all five CSVs, joins them on API Name, and produces a valid api-data.json ready to load in the catalog. Full usage in the script header.


