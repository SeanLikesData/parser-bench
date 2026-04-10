"""
Test definitions for both standard and hard benchmark suites.
"""

# ── Standard suite ──────────────────────────────────────────────
# Each entry maps a PDF filename to label, description, and
# expected phrases for content accuracy checking.

STANDARD_TESTS = {
    "sample_w9.pdf": {
        "label": "IRS W-9 Form",
        "description": "Complex form with fields, checkboxes, instructions",
        "expected": [
            "Request for Taxpayer", "Identification Number", "Certification",
            "Form W-9", "Department of the Treasury", "Internal Revenue Service",
            "Employer identification number", "Social security number",
            "Exempt payee code", "backup withholding", "FATCA",
            "www.irs.gov/FormW9", "penalties of perjury",
        ],
    },
    "sample_report.pdf": {
        "label": "Financial Report",
        "description": "Narrative text + tabular quarterly data",
        "expected": [
            "Annual Financial Report", "Executive Summary", "revenue increased",
            "$4.2 billion", "Operating margins", "Cloud Services",
            "Enterprise SW", "North America", "Asia-Pacific",
            "Year-over-Year Growth", "$1,316", "$4,200",
        ],
    },
    "complex_multicolumn.pdf": {
        "label": "Multi-Column Paper",
        "description": "Two-column academic paper layout",
        "expected": [
            "distributed computing", "quantum-resistant", "cryptographic",
            "multi-party computation", "O(n log n)", "Lattice-based",
            "CRYSTALS-Kyber", "CRYSTALS-Dilithium", "HybridMPC",
            "Ring-LWE", "SPHINCS+", "Chen et al",
        ],
    },
    "complex_tables.pdf": {
        "label": "Employee Database",
        "description": "Dense tabular data with pivot table",
        "expected": [
            "Sarah Chen", "Senior Engineer", "$185,000", "Platform",
            "Fatima Ali", "Principal Engineer", "$248,000",
            "DEPARTMENT SUMMARY", "Total Employees: 20",
            "Average Salary", "Headcount Growth", "% of Budget",
        ],
    },
    "complex_minutes.pdf": {
        "label": "Board Minutes (4pg)",
        "description": "Multi-page structured document with headers/footers",
        "expected": [
            "Board Meeting Minutes", "CEO REPORT", "CFO REPORT", "CTO REPORT",
            "$1.178B", "99.97%", "Project Aurora", "DataFlow Analytics",
            "$850M", "CONFIDENTIAL", "ACTION ITEMS", "AI-001",
            "Meeting adjourned", "APPROVED",
        ],
    },
    "hard_watermark_financial.pdf": {
        "label": "Watermarked Financial (HARD)",
        "description": "Watermark text overlapping dense financial projections + sensitivity table",
        "expected": [
            "PRIVILEGED & CONFIDENTIAL", "Morrison & Foerster", "Financial Projections",
            "$42,150", "$96,436", "EBITDA", "($16,860)", "($30,919)",
            "WACC Assumptions", "Terminal Growth Rate: 3.0%",
            "Enterprise Value Range", "EV/Revenue: 3.5x",
            "SENSITIVITY ANALYSIS", "10.5%", "$182",
            "ASC 718", "IRC Sec 199A", "H.R. 4521",
            "DRAFT", "CONFIDENTIAL", "DO NOT DISTRIBUTE",
        ],
    },
    "hard_clinical_table.pdf": {
        "label": "Clinical Trial Table (HARD)",
        "description": "Dense bordered table with section headers, subgroups, statistical data",
        "expected": [
            "PHASE III RANDOMIZED", "NCT-2025-0847", "AcmePharma",
            "Overall Response Rate", "68.2%", "31.4%", "+36.8%", "<0.001",
            "Complete Response", "22.1%", "Median PFS", "14.2",
            "Median OS", "24.6", "18.1", "Duration of Response",
            "SAFETY PROFILE", "42.1%", "Fatal AE", "1.2%", "0.8%",
            "SUBGROUP ANALYSES", "PD-L1 >=50%", "78.9%",
            "ECOG 0", "74.1%", "Bonferroni",
            "Progression-Free Survival", "Number Needed to Treat",
        ],
    },
    "hard_compliance.pdf": {
        "label": "Tax Compliance (HARD)",
        "description": "Dense structured data with formulas, special references, currency formats",
        "expected": [
            "INTERNATIONAL COMPLIANCE", "OECD Model Tax Convention",
            "US-Germany (DTAA)", "Div: 5%/15%", "Int: 0%", "Roy: 0%",
            "US-Japan (DTAA)", "Int: 10%", "US-Singapore", "Int: 12%",
            "TRANSFER PRICING", "Comparable Uncontrolled Price",
            "$12.50-$14.80/unit", "Berry Ratio", "1.08-1.22",
            "Effective Tax Rate", "22.14%",
            "Permanent Establishment Risk", "PErs = w1(days/183)",
            "0.387", "GILTI Inclusion", "IRC 951A",
            "$8,450,000", "13.125%",
            "26 U.S.C. 482", "Commissioner v. Sunnen", "333 U.S. 591",
        ],
    },
    "hard_insurance.pdf": {
        "label": "Insurance Policy 2-Col (HARD)",
        "description": "Two-column dense legal text with defined terms, tiny footer",
        "expected": [
            "COMMERCIAL GENERAL LIABILITY", "CGL-2025-048721",
            "COVERAGE A", "BODILY INJURY", "PROPERTY DAMAGE",
            "Insuring Agreement", "legally obligated", "right and duty to defend",
            "occurrence", "coverage territory", "policy period",
            "Expected Or Intended Injury", "reasonable force",
            "Contractual Liability", "insured contract",
            "Liquor Liability", "intoxication", "alcoholic beverages",
            "COVERAGE B", "PERSONAL AND ADVERTISING INJURY",
            "Each Occurrence $1,000,000", "General Aggregate $2,000,000",
            "Form CG 00 01 04 13", "Page 1 of 16",
        ],
    },
}


# ── Hard suite ──────────────────────────────────────────────────
# Each entry defines targeted quality tests (reading order,
# numeric extraction, table row integrity, etc.).

HARD_TESTS = [
    {
        "file": "hard_watermark_financial.pdf",
        "label": "Watermarked Financial Projections",
        "pages_limit": None,
        "tests": [
            {
                "name": "Watermark vs Content Separation",
                "type": "watermark",
                "content_phrases": ["Revenue", "$42,150", "EBITDA", "Net Income", "$3,617", "WACC Assumptions"],
                "watermark_phrases": ["DRAFT", "CONFIDENTIAL", "DO NOT DISTRIBUTE"],
            },
            {
                "name": "Financial Numbers Intact",
                "type": "numeric",
                "expected": [
                    "$42,150", "$96,436", "($16,860)", "$8,430", "($2,108)", "$6,323",
                    "($1,500)", "$4,823", "($1,206)", "$3,617", "22.9%", "60.0%", "20.0%",
                ],
            },
            {
                "name": "Sensitivity Table Rows",
                "type": "table",
                "rows": [
                    ["8.0%", "$232", "$248", "$267", "$291", "$320"],
                    ["9.0%", "$200", "$212", "$225", "$242", "$262"],
                    ["10.5%", "$165", "$173", "$182", "$193", "$206"],
                ],
            },
            {
                "name": "Reading Order (narrative flow)",
                "type": "order",
                "phrases": [
                    "PRIVILEGED", "Financial Projections", "Revenue", "COGS",
                    "EBITDA", "Net Income", "SENSITIVITY ANALYSIS", "10.5%",
                ],
            },
        ],
    },
    {
        "file": "hard_clinical_table.pdf",
        "label": "Clinical Trial Table",
        "pages_limit": None,
        "tests": [
            {
                "name": "Table Row Integrity (values on same line)",
                "type": "table",
                "rows": [
                    ["Overall Response Rate", "68.2%", "31.4%"],
                    ["Complete Response", "22.1%", "5.0%"],
                    ["Median PFS", "14.2", "6.8"],
                    ["Fatal AE", "1.2%", "0.8%"],
                    ["PD-L1 >=50%", "78.9%", "38.2%"],
                ],
            },
            {
                "name": "All Statistical Values Present",
                "type": "numeric",
                "expected": [
                    "68.2%", "31.4%", "+36.8%", "30.1-43.5", "<0.001",
                    "22.1%", "14.2", "6.8", "24.6", "18.1",
                    "42.1%", "28.3%", "1.2%", "0.8%",
                    "78.9%", "55.4%", "74.1%", "61.5%",
                ],
            },
            {
                "name": "Section Order",
                "type": "order",
                "phrases": [
                    "PRIMARY ENDPOINTS", "Overall Response", "SECONDARY ENDPOINTS",
                    "Duration of Response", "SAFETY PROFILE", "Fatal AE",
                    "SUBGROUP ANALYSES", "PD-L1",
                ],
            },
        ],
    },
    {
        "file": "hard_compliance.pdf",
        "label": "Tax Compliance Report",
        "pages_limit": None,
        "tests": [
            {
                "name": "Treaty Table Rows",
                "type": "table",
                "rows": [
                    ["US-Germany", "5%/15%", "0%"],
                    ["US-Japan", "5%/10%", "10%"],
                    ["US-Singapore", "5%/15%", "12%"],
                ],
            },
            {
                "name": "Formula & Calculation Values",
                "type": "numeric",
                "expected": [
                    "22.14%", "0.387", "$8,450,000", "$2,210,000", "$6,240,000",
                    "$3,120,000", "13.125%", "$12.50-$14.80", "1.08-1.22",
                ],
            },
            {
                "name": "Legal Citations Intact",
                "type": "numeric",
                "expected": [
                    "26 U.S.C. 482", "26 CFR 1.482-1(b)(1)", "333 U.S. 591",
                    "Commissioner v. Sunnen", "IRC 951A", "Art. 5 (PE)",
                ],
            },
        ],
    },
    {
        "file": "hard_insurance.pdf",
        "label": "Two-Column Insurance Policy",
        "pages_limit": None,
        "tests": [
            {
                "name": "Column Reading Order",
                "type": "columns",
                "left": [
                    "Insuring Agreement", "legally obligated", "right and duty to defend",
                    "occurrence", "coverage territory", "Expected Or Intended",
                ],
                "right": [
                    "Contractual Liability", "absence of the contract", "insured contract",
                    "Liquor Liability", "intoxication", "COVERAGE B",
                ],
            },
            {
                "name": "Defined Terms Present",
                "type": "numeric",
                "expected": [
                    '"bodily injury"', '"property damage"', '"occurrence"',
                    '"coverage territory"', '"suit"', '"insured contract"',
                    '"personal and advertising injury"',
                ],
            },
            {
                "name": "Footer Data Intact",
                "type": "numeric",
                "expected": [
                    "$1,000,000", "$100,000", "$5,000", "$2,000,000",
                    "CG 00 01 04 13", "Page 1 of 16",
                ],
            },
        ],
    },
    {
        "file": "hard_fed_report.pdf",
        "label": "Fed Financial Stability Report (real)",
        "pages_limit": 8,
        "tests": [
            {
                "name": "Key Content Present",
                "type": "numeric",
                "expected": [
                    "Financial Stability", "Federal Reserve", "monetary policy",
                    "inflation", "banking", "credit", "leverage",
                ],
            },
            {
                "name": "Reading Order",
                "type": "order",
                "phrases": ["Financial Stability", "Contents", "Overview"],
            },
        ],
    },
    {
        "file": "hard_census.pdf",
        "label": "Census Bureau Operational Plan (real)",
        "pages_limit": 8,
        "tests": [
            {
                "name": "Key Content Present",
                "type": "numeric",
                "expected": ["Census", "2020", "operational", "plan"],
            },
            {
                "name": "Reading Order",
                "type": "order",
                "phrases": ["Census", "2020"],
            },
        ],
    },
]
