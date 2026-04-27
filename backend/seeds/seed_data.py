"""
Seed script — populates the DB with 15 Policies, 8 Clients, and 8 Quotes.

Idempotent: skips all inserts if policies already exist.

Run from inside the backend container:
    python seeds/seed_data.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select

from app.core.db import engine
from app.models import Client, Policy, ProductType, Quote, QuoteStatus


# ---------------------------------------------------------------------------
# Seed data
# Each policy has a "key" used only for referencing in QUOTES below.
# The key is not persisted to the database.
# ---------------------------------------------------------------------------

POLICIES: list[dict] = [
    {
        "key": "vero_pl_2m",
        "product_type": ProductType.public_liability,
        "insurer": "Vero Insurance NZ",
        "sum_insured_nzd": 2_000_000,
        "description": (
            "Comprehensive public liability cover for small-to-medium businesses operating in New Zealand. "
            "Covers legal liability for bodily injury or property damage caused to third parties during the course of business operations, "
            "including on-site and off-site incidents. Includes product liability for goods sold or supplied. "
            "Exclusions: intentional acts, contractual liability beyond what would exist at law, asbestos-related claims, "
            "and damage to property in the insured's care, custody or control."
        ),
    },
    {
        "key": "iag_pl_5m",
        "product_type": ProductType.public_liability,
        "insurer": "IAG New Zealand",
        "sum_insured_nzd": 5_000_000,
        "description": (
            "High-limit public liability policy designed for larger commercial operations, events, and hospitality businesses. "
            "Covers claims arising from personal injury, property damage, and advertising injury. "
            "Includes defence costs in addition to the limit of indemnity. Suitable for businesses with significant foot traffic "
            "such as cafes, restaurants, retail stores, and event venues. "
            "Exclusions: professional advice or services (see professional indemnity), pollution events, and cyber incidents."
        ),
    },
    {
        "key": "zurich_pl_1m",
        "product_type": ProductType.public_liability,
        "insurer": "Zurich New Zealand",
        "sum_insured_nzd": 1_000_000,
        "description": (
            "Entry-level public liability policy for sole traders, contractors, and micro-businesses in New Zealand. "
            "Provides cover for third-party bodily injury and property damage claims up to NZ$1 million. "
            "Includes legal defence costs. Suitable for low-risk occupations such as consultants, cleaners, and tradespeople. "
            "Exclusions: damage to client property in the insured's possession, motor vehicle liability, employer's liability, "
            "and any claims arising from professional advice."
        ),
    },
    {
        "key": "qbe_pi_1m",
        "product_type": ProductType.professional_indemnity,
        "insurer": "QBE Insurance Australia/NZ",
        "sum_insured_nzd": 1_000_000,
        "description": (
            "Professional indemnity insurance for service-based businesses providing advice, design, or consulting services. "
            "Covers claims arising from actual or alleged negligent acts, errors, or omissions in the performance of professional services. "
            "Includes breach of professional duty, defamation, and intellectual property infringement arising from professional activities. "
            "Run-off cover available for retired professionals. "
            "Exclusions: known claims at inception, fraud and dishonesty, bodily injury and property damage (refer public liability), "
            "and insolvency of the insured."
        ),
    },
    {
        "key": "vero_pi_2m",
        "product_type": ProductType.professional_indemnity,
        "insurer": "Vero Insurance NZ",
        "sum_insured_nzd": 2_000_000,
        "description": (
            "Mid-market professional indemnity policy tailored for technology firms, accountants, engineers, and architects. "
            "Covers claims for financial loss suffered by clients due to negligent advice or work product. "
            "Automatic retroactive cover for prior acts. Includes regulatory investigation defence costs. "
            "Sub-limits apply for breach of confidentiality and intellectual property disputes. "
            "Exclusions: contractual penalties and liquidated damages, intentional misconduct, and claims brought by associated entities."
        ),
    },
    {
        "key": "chubb_pi_5m",
        "product_type": ProductType.professional_indemnity,
        "insurer": "Chubb Insurance NZ",
        "sum_insured_nzd": 5_000_000,
        "description": (
            "Premium professional indemnity coverage for large professional services firms including law firms, financial advisors, "
            "and management consultancies. Policy limit of NZ$5 million any one claim and in the aggregate. "
            "Broad coverage including project management liability, network security liability emanating from professional services, "
            "and employee dishonesty in the course of professional activities. Worldwide jurisdiction. "
            "Exclusions: known circumstances, insolvency of clients if foreseeable, and war or terrorism."
        ),
    },
    {
        "key": "marsh_cyber_500k",
        "product_type": ProductType.cyber,
        "insurer": "Marsh New Zealand / Beazley",
        "sum_insured_nzd": 500_000,
        "description": (
            "Cyber liability and data breach response policy for SMEs operating in New Zealand. "
            "Covers costs associated with a data breach including notification costs, credit monitoring for affected individuals, "
            "forensic investigation, and regulatory fines under the New Zealand Privacy Act 2020. "
            "Also covers business interruption losses caused by a cyber attack or ransomware event. "
            "Includes 24/7 incident response hotline and access to pre-approved cyber security vendors. "
            "Exclusions: unencrypted portable devices, known vulnerabilities not patched within 30 days of discovery, "
            "and bodily injury or physical property damage."
        ),
    },
    {
        "key": "zurich_cyber_2m",
        "product_type": ProductType.cyber,
        "insurer": "Zurich New Zealand",
        "sum_insured_nzd": 2_000_000,
        "description": (
            "Comprehensive cyber risk policy for mid-to-large enterprises handling significant volumes of personal or financial data. "
            "First-party coverage: ransomware payment costs, system restoration, business interruption, and reputational harm expenses. "
            "Third-party coverage: data breach liability, network security liability, and media liability. "
            "Includes social engineering fraud cover up to NZ$250,000. Proactive risk management services included. "
            "Exclusions: infrastructure failure caused by state-sponsored attacks (write-back available), "
            "bodily injury, and prior known incidents."
        ),
    },
    {
        "key": "aig_cyber_1m",
        "product_type": ProductType.cyber,
        "insurer": "AIG New Zealand",
        "sum_insured_nzd": 1_000_000,
        "description": (
            "Cyber insurance for professional services firms and healthcare providers in New Zealand. "
            "Specifically designed to address Privacy Act obligations, including mandatory breach notifications to the Office of the Privacy Commissioner. "
            "Covers privacy breach liability, regulatory defence and penalties, patient/client notification costs, and crisis management PR expenses. "
            "Includes business email compromise cover up to NZ$100,000. "
            "Exclusions: criminal acts by directors, war and hostile nation-state attacks without write-back, "
            "and pre-existing malware infections."
        ),
    },
    {
        "key": "iag_bi_500k",
        "product_type": ProductType.business_interruption,
        "insurer": "IAG New Zealand",
        "sum_insured_nzd": 500_000,
        "description": (
            "Business interruption insurance for retail and hospitality businesses in New Zealand. "
            "Covers loss of gross profit and continuing fixed expenses following physical damage to insured premises "
            "caused by an insured event (fire, flood, storm, earthquake). Indemnity period up to 12 months. "
            "Includes cover for loss of attraction if a neighbouring property suffers damage. "
            "Exclusions: pandemic and infectious disease (unless endorsed), cyber events, "
            "consequential loss from contract disputes, and losses not arising from a physical damage trigger."
        ),
    },
    {
        "key": "vero_bi_1m",
        "product_type": ProductType.business_interruption,
        "insurer": "Vero Insurance NZ",
        "sum_insured_nzd": 1_000_000,
        "description": (
            "Business interruption policy for manufacturing and logistics businesses with extended supply chains. "
            "Covers loss of revenue and additional costs incurred to maintain operations following a material damage event at the insured's premises "
            "or at a key supplier's or customer's premises (contingent business interruption). Indemnity period up to 24 months. "
            "Includes prevention of access cover for government-mandated closures following a nearby insured event. "
            "Exclusions: financial loss not caused by physical damage, losses arising from cyber events unless separately endorsed, "
            "and losses from utility failure unless caused by direct physical damage."
        ),
    },
    {
        "key": "qbe_bi_2m",
        "product_type": ProductType.business_interruption,
        "insurer": "QBE Insurance Australia/NZ",
        "sum_insured_nzd": 2_000_000,
        "description": (
            "High-capacity business interruption policy for large commercial and industrial businesses across New Zealand. "
            "Provides cover for gross profit loss and increased cost of working for up to 36 months following an insured material damage event. "
            "Earthquake damage cover aligned with the EQC Act, with top-up indemnity applying beyond EQC thresholds. "
            "Includes denial of access, utilities failure (direct damage), and contingent BI for named suppliers. "
            "Exclusions: losses not arising from physical loss or damage to property, contractual penalties, "
            "and losses caused by pandemics or communicable disease outbreaks."
        ),
    },
    {
        "key": "chubb_pl_10m",
        "product_type": ProductType.public_liability,
        "insurer": "Chubb Insurance NZ",
        "sum_insured_nzd": 10_000_000,
        "description": (
            "Major accounts public liability policy for large corporates, construction firms, and infrastructure operators in New Zealand. "
            "NZ$10 million limit any one occurrence and in the aggregate. Covers bodily injury, property damage, personal injury, "
            "and advertising injury to third parties. Includes products completed operations liability and cross liability clause. "
            "Worldwide coverage for exported products and offshore operations. "
            "Exclusions: employer's liability, professional errors and omissions, pollution unless sudden and accidental, "
            "and motor vehicle operations on public roads."
        ),
    },
    {
        "key": "berkley_pi_500k",
        "product_type": ProductType.professional_indemnity,
        "insurer": "Berkley Insurance",
        "sum_insured_nzd": 500_000,
        "description": (
            "Affordable professional indemnity cover designed for start-ups, freelancers, and small digital agencies in New Zealand. "
            "Covers claims for negligent acts, errors or omissions in design, development, and digital marketing services. "
            "Includes intellectual property infringement and breach of confidentiality cover. "
            "Monthly premium payment option available. "
            "Exclusions: claims arising from wilful breach of contract, prior acts before 12 months of policy inception, "
            "and bodily injury or property damage."
        ),
    },
    {
        "key": "chubb_cyber_5m",
        "product_type": ProductType.cyber,
        "insurer": "Chubb Insurance NZ",
        "sum_insured_nzd": 5_000_000,
        "description": (
            "Enterprise-grade cyber insurance for large financial institutions, insurers, and listed companies in New Zealand. "
            "Broad coverage including ransomware and extortion, system failure business interruption, third-party data breach liability, "
            "and regulatory fines under GDPR and the NZ Privacy Act 2020. Includes board advisory services and reputational harm mitigation. "
            "Silent cyber coverage clarification included as standard. Coverage for cloud service provider outages (non-physical BI). "
            "Exclusions: deliberate acts by the insured, infrastructure war (write-back available by endorsement), "
            "and losses arising from failure to maintain industry-standard security controls."
        ),
    },
]

CLIENTS: list[dict] = [
    {
        "name": "Kiwi Café Group Ltd",
        "industry": "Hospitality",
        "annual_turnover_nzd": 850_000,
        "notes": "Operates 3 cafés in Auckland CBD. High foot traffic, food handling. Concerned about public liability and cyber POS breaches.",
    },
    {
        "name": "Tāwhirimātea Engineering",
        "industry": "Engineering Consulting",
        "annual_turnover_nzd": 3_200_000,
        "notes": "Civil and structural engineering firm. Works on infrastructure projects. Requires PI cover for design errors.",
    },
    {
        "name": "Southern Cross Digital",
        "industry": "Technology / SaaS",
        "annual_turnover_nzd": 1_500_000,
        "notes": "B2B SaaS company storing customer financial data. Priority: cyber cover and PI for software defects.",
    },
    {
        "name": "Rangitoto Logistics",
        "industry": "Logistics & Distribution",
        "annual_turnover_nzd": 12_000_000,
        "notes": "National freight and warehousing operator. Needs BI cover with contingent supplier extension and high PL limits.",
    },
    {
        "name": "Pōhutukawa Accounting Partners",
        "industry": "Professional Services – Accounting",
        "annual_turnover_nzd": 900_000,
        "notes": "Mid-size accounting firm with 12 staff. Handles tax, audit, and financial advisory. Core need: professional indemnity.",
    },
    {
        "name": "Hauturu Construction Ltd",
        "industry": "Construction",
        "annual_turnover_nzd": 6_500_000,
        "notes": "Residential and light commercial builder. Requires public liability with products/completed ops and BI cover.",
    },
    {
        "name": "Manuka Health Clinic",
        "industry": "Healthcare",
        "annual_turnover_nzd": 2_100_000,
        "notes": "Multi-practitioner GP and allied health clinic. Stores patient data. Key risks: cyber/Privacy Act liability and PI.",
    },
    {
        "name": "Aotearoa Retail Holdings",
        "industry": "Retail",
        "annual_turnover_nzd": 4_700_000,
        "notes": "Chain of 8 homewares retail stores. POS systems hold card data. Needs PL, cyber, and BI for store closures.",
    },
]

# Quotes reference clients by name and policies by key — no positional indexing.
QUOTES: list[dict] = [
    {"client": "Kiwi Café Group Ltd",           "policy": "vero_pl_2m",       "premium_nzd": 1_200, "status": QuoteStatus.sent},
    {"client": "Kiwi Café Group Ltd",           "policy": "marsh_cyber_500k", "premium_nzd":   980, "status": QuoteStatus.draft},
    {"client": "Tāwhirimātea Engineering",      "policy": "qbe_pi_1m",        "premium_nzd": 4_500, "status": QuoteStatus.accepted},
    {"client": "Southern Cross Digital",        "policy": "zurich_cyber_2m",  "premium_nzd": 3_200, "status": QuoteStatus.sent},
    {"client": "Rangitoto Logistics",           "policy": "vero_bi_1m",       "premium_nzd": 8_700, "status": QuoteStatus.draft},
    {"client": "Pōhutukawa Accounting Partners","policy": "vero_pi_2m",       "premium_nzd": 2_800, "status": QuoteStatus.accepted},
    {"client": "Hauturu Construction Ltd",      "policy": "chubb_pl_10m",     "premium_nzd": 6_100, "status": QuoteStatus.sent},
    {"client": "Manuka Health Clinic",          "policy": "aig_cyber_1m",     "premium_nzd": 2_400, "status": QuoteStatus.draft},
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------

def seed() -> None:
    with Session(engine) as session:
        if session.exec(select(Policy)).first():
            print("Seed data already present — skipping.")
            return

        # Insert policies; build a lookup map by key for quote wiring.
        policies_by_key: dict[str, Policy] = {}
        for p in POLICIES:
            key = p["key"]
            policy = Policy(**{k: v for k, v in p.items() if k != "key"})
            session.add(policy)
            policies_by_key[key] = policy
        session.flush()  # assigns IDs without committing

        # Insert clients; build a lookup map by name for quote wiring.
        clients_by_name: dict[str, Client] = {}
        for c in CLIENTS:
            client = Client(**c)
            session.add(client)
            clients_by_name[c["name"]] = client
        session.flush()

        # Insert quotes using named references instead of positional indexes.
        for q in QUOTES:
            client = clients_by_name[q["client"]]
            policy = policies_by_key[q["policy"]]
            session.add(Quote(
                client_id=client.id,
                policy_id=policy.id,
                premium_nzd=q["premium_nzd"],
                status=q["status"],
            ))

        session.commit()
        print(
            f"Seeded {len(policies_by_key)} policies, "
            f"{len(clients_by_name)} clients, "
            f"{len(QUOTES)} quotes."
        )


if __name__ == "__main__":
    seed()
