# TEM Industry Playbook: standards, competitors, workflows, UX, and rebuild plan for Presence360

*Prepared 2026-10-15 for the Presence360 (P360) rescue. Anchor client is a global executive-search firm on Verizon Business. This file is code and docs only: it holds no client dollar figures or client data.*

**How to read the sourcing.** Facts carry an inline link to their source. Items marked **[unverified]** are practitioner knowledge I could not confirm in a primary source during this research. Items marked **[vendor claim]** come from vendor marketing. Where a source could not be found (for example, an AOTMP lifecycle standard or a current TEMIA standard), the report says so instead of making one up.

**Key primary sources used throughout**
- Gartner, *Market Guide for Telecom Expense Management Services, Global*, 18 Nov 2024, G00802496 (Baldino, Ruud, Young). Vendor-distributed reprint: <https://info.sakon.com/hubfs/Market_Guide_for_Tel_802496_ndx.pdf>. A 2026 edition was published around April 2026 (<https://www.vcomsolutions.com/news/vcom-named-a-representative-vendor-in-the-gartner-2026-market-guide-for-telecom-expense-management-services>), but I could not get its text. The 2024 text is used here.
- Verizon, *United States Service Agreement Master Terms* (doc 21020818-12, © 2019–2026): <https://www.verizon.com/business/service_guide/reg/g_omt_us_services.pdf>
- Verizon, *EMEA Service Agreement Master Terms* (v0714, Denmark/Greece versions): <https://www.verizon.com/business/service_guide/reg/g_omt_emea_denmark_feb2015.pdf>
- Verizon, *Online Master Terms (US)*: <https://www.verizon.com/business/service_guide/reg/g_online_master_terms.htm>
- Verizon Enterprise Center (VEC) help: billing inquiries and disputes <https://verizon.com/business/support/vec/billing/billing-questions-credits-disputes/>, inventory <https://www.verizon.com/business/support/vec/service-management/view-inventory/>, e-billing formats <https://www.verizon.com/business/support/vec/billing/electronic-billing-emedia/>

---

## 0. Executive summary

1. **The market sees TEM as mature and commoditised. Buyers now choose on operational quality, audit accuracy and analytics.** Gartner: "The TEM service market is mature, is highly commoditized, and offers little technical or functional differentiation between providers." Differentiation comes from "operational quality, analytical and simulation capabilities". Gartner client inquiries also report "disappointment with current environments" ([Gartner 2024](https://info.sakon.com/hubfs/Market_Guide_for_Tel_802496_ndx.pdf)). A rebuilt P360 wins on **provable accuracy**: every invoice reconciled to its header total, and every claim tied to a contract page. Feature count is not where it wins.
2. **Contract-aware three-way match is the core of every serious platform.** The three sides are invoice, contract/rate and inventory. Sakon names it a "three-way match" against "the contract and current inventory" ([Sakon/Goldman Sachs](https://www.sakon.com/resource/how-goldman-sachs-transformed-its-global-telecom-spend-management-practice-with-sakon)). Calero: "Every charge is validated against what was ordered, delivered, and contracted" ([Calero](https://www.calero.com/telecom-auditing)). P360 skipped inventory and contract resolution, and that is where its false positives came from.
3. **Dispute windows are short and they are hard deadlines.** Verizon US Master Terms §2.7 says an invoice is "deemed to be correct and binding" if no dispute is raised "within six months after the Due Date". The EMEA terms say six months from the **invoice date**, and only disputes raised within **30 days** may be withheld. The EMEA terms also say "Verizon's determination of Disputed Amounts is final" ([US](https://www.verizon.com/business/service_guide/reg/g_omt_us_services.pdf), [EMEA](https://www.verizon.com/business/service_guide/reg/g_omt_emea_denmark_feb2015.pdf)). A negotiated enterprise agreement can override these terms, so read the client's signed agreement first. Claims past their window lose their billing-claim status, but they still work as **negotiation leverage** at renewal.
4. **Renewal is when the money moves.** Verizon's default commercial levers are 75% Underutilization Charges on Volume Commitment shortfalls, 75% Early Termination Charges on remaining Service Commitment recurring charges, auto-renewal of some services with a 10% uplift if the customer opts out, and price changes on 30 days' notice once commitments expire (US Master Terms §§2.1, 2.10, 3.5.3). The renewal pack has to quantify each of these.
5. **AI in TEM has so far meant conversational analytics on top of invoice data, not auditing.** Calero Assistant shipped in Feb 2026 ([Calero](https://www.calero.com/blog/calero-launches-calero-assistant-conversational-intelligence-for-telecom-and-mobility)) and Tangoe AI Assistant in 2026 ([Tangoe](https://www.tangoe.com/news/tangoe-reports-first-half-2026-momentum-driven-by-larger-enterprise-commitments-and-rising-demand-for-advisory-services/)). AI also shows up in ingestion: Cass trained "ML algorithms to extract and interpret invoice data, including from … unstructured PDF files" (Gartner 2024). Contract abstraction into an evidence-linked rate schema, scored by confidence tier, is still an open space where a focused product can lead.

---

## 1. Industry standards, lifecycle and nomenclature

### 1.1 Is there a formal standard?

- **AOTMP.** AOTMP publishes the *Efficiency First®* framework, described as "a proven methodology designed to improve technology management performance". It runs certifications, including a 2025/26 "AI for Technology Management Applied Certification" ([aotmp.com](https://aotmp.com/)). An AOTMP patent describes the framework as six phases: needs assessment, baseline measurement, gap analysis, improvement execution, improvement validation, and business needs alignment ([USPTO 8775233](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8775233)). I found **no public AOTMP document that defines a normative TLM lifecycle or a billing-error taxonomy**. AOTMP's standards and best-practice library is member-gated **[unverified content]**.
- **TEMIA / TEMA.** I could not verify that a TEM industry association publishes standards today. Network World reported the formation of a TEM trade association (TEMA) aimed at "billing and dispute issues" ([Network World](https://www.networkworld.com/article/842209/lan-wan-rating-the-carriers.html)). The industry body ETMA pushed carriers toward EDI billing standardisation and noted that "how they implement it can vary wildly" ([ETMA](https://etma.org/?p=9971)). **[unverified]**: TEMIA (Telecom Expense Management Industry Association) was active around 2008–2014. I found no current standard from it.
- **Gartner is the de facto reference for scope.** Its seven **mandatory features** for TEM services are: sourcing, procurement and vendor management; ordering and provisioning management; inventory management; invoice and contract management; usage management; dispute management; reporting and BI. Its **common features** are adjacent expense management, cloud and consumption inventory, UCaaS, and IoT ([Gartner 2024](https://info.sakon.com/hubfs/Market_Guide_for_Tel_802496_ndx.pdf)).
- **Data-format standards actually exist, and they matter more.** These are ANSI X12 **EDI 811** (Consolidated Service Invoice/Statement), **EDIFACT INVOIC** (the European telecom EDI billing standard), and **TM Forum TMF678** Customer Bill Management API (v5.0.0, 2023). Details are in §1.5.
- **MetrixData360 / ISG / Everest.** MetrixData 360 is a software-asset-management (Microsoft/SAM) firm, not a TEM analyst ([CB Insights](https://www.cbinsights.com/compare/metrixdata-360-vs-redwood-compliance)). I could not find a 2025 Everest PEAK Matrix or an ISG Provider Lens dedicated to TEM **[not found]**. Gartner's Market Guide (2024; 2026 edition paywalled) is the authoritative analyst view.

### 1.2 The TEM / Telecom Lifecycle Management (TLM) lifecycle

This is a practitioner synthesis consistent with Gartner's mandatory features and TEM stack (UI, core services, automation/integration, data/analytics). It is not an official standard.

| # | Stage | What happens | Key artefacts | Who owns it |
|---|---|---|---|---|
| 1 | **Sourcing / RFP** | Requirements, carrier selection, benchmark, negotiation | RFP, bids, master agreement (MSA/USSA), amendments, pricing attachments | Procurement + Telecom mgr |
| 2 | **Procurement / ordering (MACD)** | Quote → order → install. MACD = Move, Add, Change, Delete/Disconnect | Quote, **SOF** (Service Order Form), order confirmation, FOC/install date, **Activation Date** | Telecom mgr |
| 3 | **Inventory** | Living record of every billed and installed service: circuit IDs, site, speed, term, contract | Inventory DB, carrier inventory reports, **CSR**, circuit/service IDs | Telecom mgr / TEM |
| 4 | **Invoice processing** | Ingest (EDI/e-bill/PDF/portal), normalise, validate header totals, code to GL | Invoice, BAN, line items, taxes | AP / TEM |
| 5 | **Audit** | Rate validation (contract), inventory validation (billed vs ordered), proration, tax checks, trend/variance | Exceptions with evidence | TEM analyst / auditor |
| 6 | **Dispute** | File claim → carrier acknowledges → resolve (credit / deny / partial) → verify credit applied | Dispute ticket, evidence pack, carrier claim number | TEM analyst |
| 7 | **Allocation / chargeback** | Split cost to cost centres, entities, sites, GL accounts | GL coding rules, allocation file | Finance |
| 8 | **Payment** | Approve → pay (withhold disputed amounts within the window) | AP file, payment remittance | AP |
| 9 | **Optimisation** | Remove zombies, right-size bandwidth, migrate tech (MPLS → SD-WAN/DIA), re-term | Optimisation recommendations | Telecom mgr |
| 10 | **Reporting** | Spend by service/country/site, savings, dispute pipeline | Dashboards, QBR pack | All |
| 11 | **Contract renewal** | Baseline, benchmark, commitment/ETF analysis, negotiation pack, new amendment | Renewal pack, negotiation log, new amendment / rate exhibit | Procurement + Telecom mgr |

Then the cycle starts again: the new amendment and rate exhibit feed back into stage 5 as the new rate card.

### 1.3 Vocabulary (precise definitions)

Verizon contract terms are quoted from Verizon's own definitions where possible ([US Master Terms](https://www.verizon.com/business/service_guide/reg/g_omt_us_services.pdf), "Definitions").

**Account and document identity**

| Term | Definition | Notes for P360 |
|---|---|---|
| **BAN** (Billing Account Number) | The carrier's account that an invoice is issued against. One BAN → many invoices over time → many services. | Primary key for the invoice series. Verizon international invoices may show several references (account, invoice no., customer no.). Store each one with a type. |
| **Invoice number / statement** | One billing document per BAN per bill period. A US "statement" can roll up several sub-accounts. | Header total = Σ lines + taxes − credits ± adjustments. **Must reconcile to the cent.** |
| **Circuit ID / Service ID** | Carrier's identifier for a physical or logical service (access circuit, port, PVC/EVC, managed device). | Join key between invoice line ↔ inventory ↔ SOF. Normalise punctuation and case. Keep the raw value too. |
| **CSR** (Customer Service Record) | Carrier's record of every billable element on an account: USOC/feature codes, quantities, rates, install dates. Historically a US ILEC/local-services artefact. | For Verizon Business global data services, the closest equivalents are VEC **Service inventory reports** (Access Detail, Service Detail, Managed Service Details, PVC-EVC Details) ([VEC](https://www.verizon.com/business/support/vec/service-management/view-inventory/)) plus the contract/pricing summary held by the account team. Ask for both. |
| **USOC** | Universal Service Order Code: billing element code on US local and access services. | Calero lets disputes drill "down to the USOC" ([Calero](https://www.calero.com/telecom-auditing)). |
| **NPA-NXX / CLLI** | US area code + exchange / location code for central offices. | Pricing schedules sometimes key on these. A missing NPA-NXX can mean ICB pricing was never applied ([Network World/TechCaliber](https://www.networkworld.com/article/942692/savings-that-telecom-expense-management-providers-miss.html)). |

**Charge types**

| Term | Definition | Notes |
|---|---|---|
| **MRC** | "Recurring Charges that are invoiced monthly". Recurring charges "accrue from the Activation Date and are invoiced in advance" (Verizon US §2.3). | Compare per service per month against the contracted rate. |
| **NRC** | "non-Recurring Charges – that is one-time Charges". NRCs "accrue from the Commencement Date and are invoiced at any time thereafter" (§2.3). | Often billed in **instalments**. Check the **cumulative** amount against the contract cap, not month by month. |
| **OCC** (Other Charges & Credits) | Out-of-cycle adjustments: partial-month charges, back-billing, credits, one-off corrections. | Most proration and credit noise lives here. Net it per service per period before comparing. |
| **Usage** | Consumption charges (minutes, GB, burst above CIR). "invoiced in arrears" (§2.3). | Different timing from MRC: usage for month M often appears on the invoice for M+1. |
| **Proration / partial month** | MRC × (days active ÷ days in period) at activation, disconnection or change. | P360 ignored this and so flagged every install and disconnect month. Rebuild every prorated amount from the dates. |
| **Back-billing** | Charges invoiced after the period in which they accrued. Verizon: "For Charges invoiced more than six months after the date a Charge accrues, Customer may obtain a credit on request" (US §2.3; EMEA §7.1 similar). | Back-billed items older than six months can be **disputed on that basis**. Underbilled (Tier D) items older than six months carry little exposure. |
| **Taxes** | Government-imposed (VAT/GST, sales tax, excise). "All Charges are exclusive of Taxes" (§2.9). | Validate rate, jurisdiction, and exemption certificate on file. |
| **Surcharges / regulatory recovery fees** | Carrier-imposed recovery charges, not taxes. Examples: Verizon **Carrier Cost Recovery Charge** ("a Company charge, not a Tax"), FUSF ([Verizon CCRC](https://www.verizon.com/business/service_guide/reg/m_ccrc.htm)). | Percentages change over time. Store them as a time-versioned table. Audit the **base** they are applied to. Tangoe sells a dedicated tax/fee audit ([Tangoe](https://www.tangoe.com/news/tangoe-reports-first-half-2026-momentum-driven-by-larger-enterprise-commitments-and-rising-demand-for-advisory-services/)). |
| **Third-party / pass-through charges** | Charges billed by Verizon on behalf of local access providers or other suppliers. Excluded from Eligible Charges "where Verizon … act as agent" (definition of Eligible Charges). | Keep these in a separate bucket. They don't count toward commitment and need different evidence. |
| **Paper invoice fee** | Online Master Terms §8.4.1: "A $40 monthly recurring charge applies to every paper invoice" (US online terms) ([Verizon online terms](https://www.verizon.com/business/service_guide/reg/g_online_master_terms.htm)). | Quick check: is the client paying for paper invoices it doesn't need? |

**Commercial and contract terms**

| Term | Definition | Notes |
|---|---|---|
| **MSA / USSA / Master Terms** | Master agreement. For Verizon US: "U.S. Service Agreement … sets out the terms that Customer and Verizon agree will apply to all Orders under it". | Global customers usually have a negotiated master agreement with country/regional terms. |
| **Amendment** | Numbered change to the master agreement: pricing, term, commitment, new services. | **Amendments supersede by number and effective date.** Build an "effective rate as of date D" resolver. |
| **Service Attachment** | "an online or paper document containing the terms for one or more Services". | Holds SLAs and service-specific rules. |
| **Pricing attachment / rate exhibit / rate card** | Price tables (port speed × country × term, access, CPE, managed tiers). | In this engagement, the rate card sits in a numbered amendment. Some products (e.g., Managed WAN, Internet Dedicated) may have separate exhibits. |
| **SOF** (Service Order Form) | "'Service Order', 'Service Order Form', or 'SOF' is a type of written Order". **NSS** = "No Sign SOF". | Per-site prices and term. Verizon US: "any Service Commitment stated in an Order will take precedence over conflicting information elsewhere" (§2.10.2.1). |
| **Order of precedence** | US: "the USSA takes precedence over Orders… Master Terms, Service Attachments and Pricing" (§17.13). Online US terms: Service Order first, then Agreement (§5) ([online terms](https://www.verizon.com/business/service_guide/reg/g_online_master_terms.htm)). | **The two Verizon documents state different orders of precedence.** The rate resolver must apply the precedence clause in the *client's* signed agreement and must not hard-code one. |
| **Activation Date / Commencement Date** | Activation is when the service is ready to route traffic, which starts MRC accrual. Commencement is when both parties are bound, which starts the order or term clock for NRCs. | Both are needed for proration and for computing the term end. |
| **Service Commitment** | "the period of time after the Activation Date for which Customer is committed to pay for a particular Service". Default minimum one year for non-Optimized services (§2.10.2.1). | Term end = Activation + commitment. This drives **ETF exposure**. |
| **Volume Commitment** (AVC / TVC / Tiered / Subminimum) | "the agreed upon Customer commitment to purchase". Verizon's equivalent of **MARC/MAC/MRC-commitment** (Minimum Annual Revenue Commitment). | Measured on **Eligible Charges**, per **Contract Year**. |
| **Eligible Charges** | All charges after discounts and credits, **excluding** taxes, CPE, agency third-party charges, NRCs, most Underutilization Charges, and Governmental Charges. | Commitment attainment must use this base, not invoice totals. |
| **Shortfall / Underutilization Charge** | "If … the Eligible Charges Customer has paid are less than the Volume Commitment, then Customer shall pay an Underutilization Charge equal to 75% of the shortfall (or other percentage…)" (§2.10.1.1). | The renewal pack must forecast attainment for the current Contract Year. |
| **ETF / Early Termination Charge** | Service: "75% … of the Recurring Charges that would have been payable … for the remaining unexpired part of the Service Commitment" (§3.5.3.1). Volume: a percentage of the shortfall in the year of termination plus a percentage of the remaining commitments (§3.5.3.3). | Moves and changes to "Optimized" (+) services can reduce the ETF by the replacement's recurring charges (§3.5.3.2). |
| **Auto-renewal** | For some services ordered after 2 Nov 2022, with no Volume Commitment: renews for one year at a time unless the customer opts out ≥30 days before expiry **via VEC form only**. Opting out raises recurring charges **by 10%** 30 days after expiry (§2.10.2.2). | Check whether the client's agreement includes this clause. Calendar it per service. |
| **Post-term pricing** | After commitment expiry, Verizon may change charges on 30 days' notice (non-voice) (§2.1). The service "continues until either Party terminates it" (§2.10.3). | Out-of-term services are exposed to unilateral price rises. Count them in the renewal pack. |
| **Achievement / attainment credits** | Credits paid when spend reaches agreed tiers, or as signing/renewal incentives. Public Verizon examples: a renewal credit of 3% of AVC, capped and paid in month 4 ([Verizon promo](https://verizon.com/business/service_guide/reg/pr_contract_renewal_promotion.htm)); 15% of total volume commitment paid in instalments for 3–5-year terms ([RVP Checkbook](https://www.verizon.com/business/service_guide/reg/pr_rvp_checkbook_3-5yr.htm)). | Exact tiers are **contract-specific**. Read them from the client's amendment. Track earned vs paid, and note that credits can be "withheld until the shortfall is paid" in some carrier contracts ([Law Insider MARC clause](https://www.lawinsider.com/clause/marc/_2)). |
| **Optimized Service** | Verizon: a service "optimized for Verizon's automation platform, which is indicated by '+' after the Service name (e.g., 'Private IP +')". | Different default commitment and ETF rules apply. Capture the "+" flag in inventory. |
| **ICB** | Individual Case Basis pricing, a one-off price outside the rate card. | Usually on an SOF. Verify it against the SOF, not the rate card. |
| **Co-terming** | Aligning service term end dates with the master agreement end date so they can all be renegotiated together. | Renewal pack: list each service's term end against the master term end. |

**Audit and operations terms**

| Term | Definition |
|---|---|
| **Inventory reconciliation** | Matching three sets: (a) what is billed, (b) what the carrier says is installed (inventory reports/CSR), (c) what the enterprise believes it has (sites, SOFs, IT records). Differences give zombies, unbilled services, duplicates, and wrong-site billing. |
| **Zombie / ghost circuit** | A service still billing after disconnection or replacement, or never used. Calero's audit "identifies unused ('zombie') services" ([Calero](https://www.calero.com/telecom-auditing)). A typical signature is two circuit IDs at one address after a migration ([PBXdom](https://www.pbxdom.com/blog/product/carrier-invoice-reconciliation-catch-billing-errors/)). |
| **Dangling services** | Access circuits billing without the MPLS port they serve, or the reverse ([Network World/TechCaliber](https://www.networkworld.com/article/942692/savings-that-telecom-expense-management-providers-miss.html)). |
| **Dispute aging** | Days since a dispute was filed (and since the invoice date), in buckets of 0–30, 31–60, 61–90 and 90+ days. Calero reports "open versus closed claims, recovered versus denied amounts, and dispute aging" ([Calero](https://www.calero.com/telecom-auditing)). |
| **Credit realisation (recovery rate)** | Credits actually **posted on an invoice** ÷ amount disputed. Only a posted credit counts as realised. A promised credit does not. |
| **Dispute win rate** | Disputes resolved in the client's favour ÷ disputes closed. One enterprise cited 71% → 94% as dispute quality improved ([No Jitter, 2012](https://www.nojitter.com/telecommunication-technology/8-metrics-for-tem)). |
| **Hard savings vs cost avoidance** | Hard savings are a measurable reduction in what is paid against a validated baseline: recurring rate cuts and disconnects. **Refunds/credits** are best reported as a separate "recovery" line. Cost avoidance is a charge that never happened, such as a price increase you negotiated away. Report the two separately ([ITAM Review](https://itassetmanagement.net/2021/05/19/cost-savings-versus-cost-avoidance/)). Gartner warns that contingency deals need clarity on "what constitutes 'savings' and how those savings are computed". |

### 1.4 Billing error taxonomy (use this as the rule-library spine)

This synthesises Network World/TechCaliber ([link](https://www.networkworld.com/article/942692/savings-that-telecom-expense-management-providers-miss.html)), Calero ([link](https://www.calero.com/telecom-auditing)) and practitioner experience. Each category maps to a rule family and a default confidence tier in P360's A–E scheme.

| Code | Category | Example | Detection rule | Default P360 tier |
|---|---|---|---|---|
| R1 | **Rate not per contract** | Port billed at list price, not the amendment rate | billed MRC > effective contract rate(service, speed, country, term, date) | A if the contract is resolved from the invoice-printed reference; B if inferred |
| R2 | **Rate not implemented** | New amendment rate never loaded into billing | billed = prior rate after amendment effective date | A |
| R3 | **Discount/waiver missing** | Access waiver in the pricing schedule but billed anyway | waiver flag in SOF/amendment and charge present | A/B |
| Q1 | **Billed after disconnect (zombie)** | MRC continues after the disconnect order date | disconnect evidence date < billed period | B (needs the disconnect order) |
| Q2 | **Duplicate billing** | Same circuit on a local and a global invoice | same service ID on 2 BANs in the same period | B |
| Q3 | **Dangling dependency** | Access without port, or port without access | inventory graph orphan | B/C |
| P1 | **Proration error** | Full month billed for a partial month | expected = rate × days/period | A when the dates are on the invoice |
| N1 | **NRC over cap / repeated** | Instalments exceed the contracted NRC | Σ instalments > NRC on SOF | A |
| T1 | **Tax/surcharge base or rate wrong** | Surcharge applied to an exempt or ineligible base | recompute from the base and the time-versioned rate | B |
| T2 | **Tax exemption ignored** | Exemption certificate on file but tax charged | cert on file and tax > 0 | B |
| C1 | **Credit not applied** | Promised dispute or SLA credit missing | dispute = approved and no matching credit within N cycles | A |
| C2 | **Achievement credit not paid** | Tier reached, credit not paid | attainment ≥ tier and no credit | C (commercial) |
| F1 | **FX / currency error** | Non-contract FX rate used | stated rate vs contract FX clause | B |
| L1 | **Late fee caused by a carrier error** | Late fee on an invoice that was disputed in time | dispute filed before due date and late fee present | A |
| B1 | **Back-billing > 6 months** | Charge for a period more than 6 months before the invoice | accrual date < invoice date − 6 mo | A (Verizon §2.3 credit-on-request) |
| U1 | **Underbilling** | Billed < contract | billed < contract rate | **D**: do not dispute. Track as exposure. |
| X1 | **Missing contract** | No SOF or price found for the service | contract resolution failed | **E**: never call this overbilling. Request the document. |
| E1 | **ETF / shortfall charge** | Termination or underutilisation charge billed | charge type ∈ {ETF, UC} | **C**: commercial review |

### 1.5 Electronic billing formats and record types

- **EDI X12 811** (Consolidated Service Invoice/Statement). It replaces paper "for very complex and structured billing". The hierarchy can reach 9 levels: service/billing provider → billing arrangement → sub-billing arrangement → group → category → subcategory → type → charge detail → line detail ([Stedi X12 811](https://www.stedi.com/edi/x12-003070/811)). Verizon publishes an 811 Implementation Guide, Change Guide and Appendix A, all v20.2 May 2020, X12 004010 ([VEC EDI guide](https://www.verizon.com/business/support/vec/onlinehelp/guidesandtutorials/billing/electronic/EDI-implementation.html)).
- **EDIFACT INVOIC.** Verizon: "EDIFACT follows the European Telecom EDI billing standard for electronic billing". There are separate guides for "PRIME Biller Next Gen" and "PRIME Biller Legacy" ([VEC eMedia](https://www.verizon.com/business/support/vec/billing/electronic-billing-emedia/)). **This is the most likely machine-readable source for the client's international invoices.** Ask Verizon which biller each BAN is on.
- **VZ450 Direct Data.** Verizon's own record-layout feed ("Customer Specifications and a Change Log") (same page).
- **VEC downloads.** PDF invoices. "Invoice Details Records (IDR), Call Details Records (CDR) and extensive billing reports are also available" ([VEC fact sheet](https://espanol2.verizon.com/business/resources/factsheets/vec-overview.pdf)).
- **CDR** (Call Detail Record): per-call or per-session usage record. For data services, "usage" usually means burst or overage records.
- **TM Forum TMF678** Customer Bill Management API: customerBill + appliedCustomerBillingRate, which carries recurring, one-time, discount and tax charges applied to products and aggregated into bills ([TM Forum](https://tmforum.org/oda/open-apis/directory/customer-bill-management-api-TMF678/v5.0.0); [TMF community](https://engage.tmforum.org/discussion/tmf-678-customerbill-applied-customer-billing-rate)). **A good internal canonical model**, even though carriers rarely expose it to enterprises.
- **Country e-invoice formats relevant to the client:**
  - **India GST** (CGST Rule 46). Required particulars include supplier GSTIN, serial number, date, recipient GSTIN, HSN/SAC, taxable value, the CGST/SGST or IGST split, and **place of supply**. E-invoices carry an IRN and a signed QR code ([summary](https://tallysolutions.com/gst/gst-invoice-format-mandatory-fields-rules-and-examples-for-businesses/)). Secondary source; check the field list against the CBIC notification. **[unverified]**: telecom services typically use SAC heading 9984.
  - **Italy FatturaPA via SDI.** TD01 = invoice, **TD04 = credit note** (reduction under art. 26 DPR 633/72), TD05 = debit note ([B2BRouter](https://docs.b2brouter.net/en/developers/mapping-guides/fatturapa-document-type-codes/); [Agenzia Entrate guide](https://www.agenziaentrate.gov.it/portale/documents/20143/451259/Guida_compilazione-FE_18+12+20.pdf/e811fe3d-332d-5b51-5990-10d7e4641164%20)). The XML is authoritative. **Ask for the SDI XML, not just the PDF render.** It parses without OCR.

---

## 2. Feature map of leading platforms

### 2.1 Market structure (2024–2026)

- **Gartner 2024 representative vendors (17):** Asignet, Avail, brightfin, Calero, Cass, ICOMM, Mindglobal, Motus, One Source, RadiusPoint, Sakon, Tangoe, Tellennium, Upland Software (Cimpl), Valicom, vCom, WidePoint ([Gartner 2024](https://info.sakon.com/hubfs/Market_Guide_for_Tel_802496_ndx.pdf)). Vendors named in the **2026 guide** by their own press releases: vCom, Tangoe, Calero, Sakon ([vCom](https://www.vcomsolutions.com/news/vcom-named-a-representative-vendor-in-the-gartner-2026-market-guide-for-telecom-expense-management-services)) and brightfin ([brightfin](https://www.brightfin.com/2026-gartner-tem-market-guide/)). The full list is **[unverified]**.
- **M&A since 2023:** Asignet acquired NTT's CLM/Xigo (Jan 2023). DMI acquired Simplex Mobility (Jan 2023) (Gartner). **Cass sold its TEM & MMS business to Asignet for $18.0M**, signed 7 Apr 2025 and closed 30 Jun 2025 ([Cass 8-K](https://www.sec.gov/Archives/edgar/data/708781/000070878125000030/cass-202503xtelecomxexx991.htm); [Cass news](https://www.cassinfo.com/news/cass-sells-telecom-expense-management-business-to-asignet)). Asignet claims "3,800+ invoice parsers operating across 90+ countries" **[vendor claim]**. **Treat "Cass" as Asignet going forward.**
- **Scale (vendor-reported to Gartner, 2024):** Calero ~$25B managed spend. Cass ~$90B spend (incl. non-telecom). Asignet $6B direct. brightfin $966M. Upland $1.9B. Valicom $550M.

### 2.2 What they actually ship (verified claims only)

| Capability | Tangoe | Calero | Sakon | Cass → Asignet | brightfin | Upland Cimpl | Valicom | Tellennium |
|---|---|---|---|---|---|---|---|---|
| Invoice ingestion | AI for "invoice loading processes" (Gartner) | AI data mapping, "AI email parsing" (Gartner) | "Intake any format" (paper, PDF, EDI, portals) ([Sakon AP](https://www.sakon.com/ap-automation)); converts non-English/non-USD bills ([GS case](https://www.sakon.com/resource/how-goldman-sachs-transformed-its-global-telecom-spend-management-practice-with-sakon)) | RPA + ML extraction from "unstructured PDF files and images" (Gartner) | Invoice lifecycle automation in ServiceNow ([ServiceNow Store](https://store.servicenow.com/store/app/506dafe21b646a50a85b16db234bcbd6)) | AI in "data ingestion, normalization" (Gartner) | n/a | n/a |
| Contract / rate audit | "price charged is per contractual terms" ([Tangoe](https://tangoe.com/telecom-expense-management/invoice-audit-optimization)) | Charges validated against "ordered, delivered, and contracted" ([Calero](https://www.calero.com/telecom-auditing)) | Three-way match: invoice vs contract vs inventory | Audit (managed service) | "configurable audit rules" (Store listing) | Audit engine (secondary listing) | Compares "invoices against contracted rates" ([listing](https://www.getapp.com/it-communications-software/a/clearview)) | **"AI contract reader for key terms identification"** (Gartner) |
| Inventory | "real-time" inventory, mapping to locations ([Tangoe One Telecom](https://www.tangoe.com/brochure/tangoe-one-telecom/)) | Install-to-invoice tracking, zombie detection, MACD reconciliation | Real-time inventory (Gartner) | Circuit inventory control (case study) | Fixed assets + services | yes | yes | Very detailed circuit inventory incl. PIC, location, MAC (Gartner) |
| Dispute workflow | Issues "prepped for dispute"; can run "the entire Dispute Management process on your behalf" | Configurable workflows, drill to USOC, aging, recovered vs denied | Creates and tracks disputes (case studies) | Dispute management (case study) | Dispute management in ServiceNow | Dispute handling (listing) | Managed service | n/a |
| GL allocation / chargeback | "full cost allocation" (Tangoe Pay) | Links assets to cost centre and contract | GL/AP/HR integrations (Gartner) | Automated chargebacks | Cost-centre access | Cost allocation and chargeback | Cost allocation | Self-service cost allocation |
| AP / bill pay | **Tangoe Pay** | n/a | **FlexPay**, 4 payment rails, 20+ currencies | Core heritage (bill pay) | Through to payment | n/a | Payment processing | n/a |
| Renewal / benchmarking | Advisory: "Rates & Savings Analysis", "market price indexes", contract negotiation | n/a | "vendor quote management" (Gartner) | Sourcing support | n/a | Vendor rationalisation | n/a | n/a |
| GenAI | **Tangoe AI Assistant** (NLQ over expense data, 2026) | **Calero Assistant** (Feb 2026, grounded in invoice data, flags disputed charges) | ServiceNow Now Assist for mobility/help desk (Gartner) | n/a | GenAI between workflows, chatbots | GenAI for content | Internal only | AI for capturing contractual commitments |

"n/a" means I found no verified public evidence. It does not mean the product lacks the feature. **Network Control** offers a managed TEM with inventory, bill audit, disputes and contract negotiation help ([profile](https://www.extruct.ai/hub/networkcontrol-com)). I could not verify a product called "Spend Advisor". **Veramark** is a Calero heritage brand and **MDSL** merged into Calero (the Calero-MDSL name appears on [CB Insights](https://www.cbinsights.com/investor/calero-mdsl)). **vTEM, Wireless Analytics, Mobile Solutions** are mostly mobility-focused. I did not research them in depth **[not verified]**.

### 2.3 Table stakes vs differentiators (my assessment for a 2026 buyer)

**Table stakes (missing any of these loses the deal):**
1. Ingest every invoice in the estate and reconcile it to the header total, with an exception queue for failures.
2. Inventory linked to invoices: service/circuit ID ↔ site ↔ BAN ↔ contract.
3. Contract rate validation (MRC/NRC) with effective dating.
4. Dispute tracking with aging, status, and credit-posted verification.
5. GL coding / allocation export and AP file.
6. Spend dashboards by vendor, service, site, country and cost centre.
7. Role-based access, SSO, audit log, and SOC 2 / ISO 27001 (Gartner lists ISO 27001/27701/SOC 2 for most vendors).

**Differentiators:**
1. **Evidence-linked findings**: every exception cites contract doc + page + clause and invoice + page + line. Few vendors advertise this publicly.
2. **Confidence-tiered findings** that separate recoverable, needs-confirmation, commercial, underbilled and unverifiable. This tackles the false-positive problem directly.
3. **Contract abstraction from scanned amendments and SOFs** into a versioned rate schema with human verification.
4. **Commitment and ETF modelling** with renewal scenario simulation. Gartner names "technology simulations" and "scenario planning" as differentiators.
5. **Dispute-window clocks** per contract, with auto-escalation before expiry.
6. Natural-language Q&A grounded in the client's own data (Calero and Tangoe now ship this, so it is becoming table stakes).
7. Multi-country tax intelligence (GST, VAT, e-invoice XML).

### 2.4 Commercial models

From the Gartner 2024 Market Guide:
- Ongoing fixed or hybrid engagements are mostly "a predetermined percentage of the spend under management". Mobile-only engagements often use "a fixed cost per device per month".
- Backward-looking **audits** use a fixed fee or **contingency at 15%–50% of savings (usually around 25% to 35%)**. Gartner notes a "pivot toward gain share".
- Average contract 12–36 months. Watch for "harsh autorenewal clauses of up to 12 months". Start renewals "up to 12 months" early for large deals.
- "Try-and-buy": a three-month contingency audit that converts to a three-year TEM contract.
- Per-invoice pricing exists in the market **[unverified]**. Gartner does not list it.

**Implication for Staqo:** for a client that is unhappy and has a renewal coming, offer a **gain-share on Tier A/B realised credits** (credits posted to the invoice, not credits "identified"). Pair it with a fixed platform fee. Agree the definition of savings in writing, as Gartner recommends.

---

## 3. Workflows in detail

### 3.1 Invoice audit → dispute → credit tracking

#### 3.1.1 Audit pipeline (per invoice)

```
Ingest ─► Identify layout ─► Extract (deterministic parser ∥ OCR+LLM) ─► Reconcile to header (to the cent)
  │                                                                             │ fail → EXTRACTION_EXCEPTION queue
  ▼
Resolve each line → Service/Circuit → Site → Contract (via invoice-printed contract/service ref, else SOF lookup, else E)
  ▼
Normalise per service × billing month: net MRC + OCC + credits; split NRC instalments, usage, taxes, pass-throughs, ETF/UC
  ▼
Price: effective rate(service, attributes, date) from SOF ▸ amendment rate card ▸ master (per precedence clause)
  ▼
Compare with proration; cumulative NRC; credit netting; back-billing age; tax base
  ▼
Classify → Tier A/B/C/D/E/OK with reason code (R1…X1) + evidence pointers
  ▼
Human verification (B→A promotion, or reject) ─► Dispute batch
```

#### 3.1.2 Dispute lifecycle states (recommended)

No published TEM standard sets status names, and I could not verify Calero's or Tangoe's exact state names. Credit-dispute systems elsewhere use outcomes such as "Upheld, Denied, or Partial" ([Access Group](https://help-collect.theaccessgroup.com/en/articles/15656394-dispute-details)). Recommended state machine:

| State | Entry criterion | Exit | Clock |
|---|---|---|---|
| `DRAFT` | Finding is Tier A, or B confirmed by an analyst | Evidence pack complete | Window deadline shown |
| `READY` | Reviewer approved (4-eyes for > threshold) | Filed with the carrier | — |
| `FILED` | Submitted in VEC (Billing > Create inquiry) or by written notice; carrier ref captured | Carrier acknowledges | Verizon targets contact "within one business day" ([VEC](https://verizon.com/business/support/vec/billing/billing-questions-credits-disputes/)) |
| `ACKNOWLEDGED` | Carrier ticket number received | Carrier responds | SLA timer, e.g. escalate at 30 days |
| `INFO_REQUESTED` | Carrier asks for more evidence | Evidence sent | Pause/track |
| `ESCALATED` | No response by SLA, or denial contested | Account team / exec sponsor response | — |
| `RESOLVED_APPROVED` / `RESOLVED_PARTIAL` / `RESOLVED_DENIED` | Carrier decision recorded with amount | Credit verification | — |
| `CREDIT_PENDING` | Approved, credit not yet seen | Credit line matched on a subsequent invoice | Alert if not seen in 2 cycles |
| `CREDIT_POSTED` (realised) | Credit line matched (amount, service, period) | Closed | — |
| `CLOSED_WITHDRAWN` | Client withdrew after new evidence | — | — |
| `EXPIRED_WINDOW` | Not filed before the contractual deadline | Moved to Negotiation Leverage list | — |
| `ROOT_CAUSE_FIXED` | Rate corrected going forward (no recurrence for N cycles) | — | Separate flag. Counts as hard savings. |

Rules:
- **A dispute is not done until the credit is posted *and* the forward rate is fixed.** Track both separately. They are the two halves of the savings.
- **Withhold disputed amounts only if the filing was timely.** Verizon US: notify by the Due Date to withhold. EMEA: within 30 days of invoice date. Undisputed amounts must still be paid (§2.7 / §7.4). Late payment accrues interest: US up to 5.0% per month compounded (§2.8); online US terms up to 1.5% per month.
- **One issue per claim, all affected invoices listed.** VEC lets you select invoices from the last six months or toggle "My inquiry requires a different timeframe" ([VEC](https://verizon.com/business/support/vec/billing/billing-questions-credits-disputes/)). File recurring errors as one dispute listing every month, and include a forward-fix request.

#### 3.1.3 Evidence pack (minimum)

1. Invoice PDF page(s) with the line highlighted. Invoice number, BAN, date, due date, line text, amount, currency.
2. Contract evidence: document ID (amendment number / SOF ID), effective date, page, clause/table row, the rate, and **why that row applies** (speed, country, access type, term).
3. Calculation: expected vs billed, proration days, FX if relevant, month-by-month table.
4. Inventory evidence where relevant: disconnect order and date, VEC inventory export row, install date.
5. Requested remedy: credit amount per invoice, **plus correction of the rate going forward**, plus late-fee reversal where relevant.
6. Contract basis for timeliness: which clause sets the window, and the filing date.

#### 3.1.4 Dispute windows and expired claims

| Source | Window | Withholding |
|---|---|---|
| Verizon **US** Master Terms §2.7 | Dispute "within six months after the **Due Date**", else "deemed to be correct and binding" | Notify by the Due Date to withhold |
| Verizon **EMEA** Master Terms v0714 §7.4 | "within six months of the date of an invoice" | Written notice "within 30 days of the invoice date" to withhold. "Verizon's determination of Disputed Amounts is final" |
| Verizon **online US** terms §9.4 | six months of invoice date | 30 days of invoice date |
| Verizon small-business ToS | 30 days after receiving the bill ([Verizon](https://www.verizon.com/about/terms/business-office-services-terms-of-service)) | — (not enterprise) |
| Older Verizon Business agreement (2000s) | 6 months from invoice date ([copy](https://wikileaks.org/gifiles/attach/150/150433_Service%20Agreement.pdf)) | — |
| Industry practice | "typically 90 to 180 days" ([vendor guide](https://www.voiceplus.com.au/services/telecom-expense-management/telecom-billing-errors)) **[vendor claim]**. TechCaliber warns against contracts limiting recovery to "less than one year" ([Network World](https://www.networkworld.com/article/942692/savings-that-telecom-expense-management-providers-miss.html)) | — |

**What to do with expired claims (the "leverage ledger"):**
- They are no longer billing disputes under the contract. They are still documented evidence of systematic billing error.
- At renewal, present them as a **goodwill/settlement credit request**: "rate X was never implemented for N months. We ask for a one-time renewal credit equal to the overcharge". Also present them as justification for a **longer dispute window** (12–24 months) and the **removal of "Verizon's determination is final"** in the new agreement.
- Never mix expired items into the Tier A claim total. Report them as a separate line: "historical overcharge outside the window".
- Back-billing works in the client's favour: charges invoiced more than six months after accrual are creditable on request (§2.3). Run that rule (B1) before every renewal.

### 3.2 Contract abstraction and rate validation

**Document hierarchy to model (Verizon-style):**
```
Master agreement (USSA / global MSA) ── Master Terms (online, versioned by date)
  ├── Service Attachments / Service Terms (online, versioned)
  ├── Amendment 1..N (numbered, effective date, may supersede pricing, term, commitment)
  │     └── Pricing attachments / rate exhibits (rate cards: product × country × speed × access × term)
  └── Orders: SOF / NSS (per site; ICB prices; Service Commitment; Activation/Commencement)
        └── MACD orders (change speed, move, disconnect)
```

**Abstraction steps:**
1. **Classify and date every document**: type, contract number, amendment number, effective date, signature status (signed vs unsigned draft), superseded-by.
2. **Extract terms** into the schema in §6.2: commitments, term, dispute window, precedence clause, ETF %, UC %, auto-renewal, price-change rights, FX clause, credits/achievement tiers, SLA credits.
3. **Extract rate tables row by row** with full dimensional keys and a **page + table + row** pointer. Never flatten a table into prose.
4. **Human verification**: a reviewer confirms each rate row against the page image, side by side. Promote it from `EXTRACTED` to `VERIFIED`. Only VERIFIED rows can produce Tier A.
5. **Effective-rate resolver**: `rate(service_attrs, date)` walks SOF (if the SOF has a price) → latest effective amendment rate card → base pricing, applying the precedence clause from the client's agreement. It returns the winning row plus the runner-up rows that were rejected and why. Show both in the UI.
6. **Contract resolution from the invoice**: prefer the contract or service reference printed on the invoice line. Fall back to SOF lookup by circuit or site. Otherwise the line is **Tier E (missing contract)**. A Tier E line is never treated as overbilling. This one rule removes P360's largest false-positive class.

**Rate validation rules:**
- Compare **per service per billing month** after netting OCC and credits. Do not compare per line.
- Proration: expected = rate × active days ÷ days-in-period. Use the carrier's convention, which may be actual days or 30. Infer it from history and confirm it.
- NRC: Σ instalments over the life ≤ contracted NRC. Do not flag each instalment.
- Price-change validity: after the commitment ends, increases are allowed on notice (US §2.1). Flag **"post-term increase: check notice"**, not "overbilling".
- Achievement credits: compute attainment on **Eligible Charges** (exclusions per the definition), per Contract Year.

### 3.3 Contract renewal / RFP preparation

#### 3.3.1 Timeline

- Gartner: start the renewal or buying process "up to 12 months" early for larger deals, and avoid "falling back into month-to-month contracts, longer-term autorenewals and worsening terms" ([Gartner 2024](https://info.sakon.com/hubfs/Market_Guide_for_Tel_802496_ndx.pdf); that advice is about TEM contracts but applies equally to carrier deals). Info-Tech: bargaining power is stronger starting "roughly 90 days prior" ([Info-Tech](https://www.infotech.com/research/renegotiating-telecom-contracts-timing-is-everything)). Tangoe: "prices tend to increase upon contract end dates" ([Tangoe](https://www.tangoe.com/blog/time-to-renegotiate-your-telecom-and-mobile-service-contracts-procurement-tips-from-tangoe)).
- **The client's renewal is next month, so this is a compressed renewal.** Options: (a) negotiate a **3–6-month extension at current rates** with no auto-renew uplift, to run a proper process, or (b) negotiate now with the pack below and keep open-dispute settlement as a condition of signing.

#### 3.3.2 Contents of a renewal negotiation pack

| # | Section | Content | Source in P360 |
|---|---|---|---|
| 1 | **Spend baseline** | 12–36 months monthly series by service family (Private IP/MPLS, Internet Dedicated, SD-WAN, Managed WAN, DNM, voice), country, site, BAN. Split into MRC, NRC, usage, taxes, pass-through, credits. Fiscal-year roll-up. | Ledger |
| 2 | **Inventory** | Every active service: circuit/service ID, site, product, speed, access type, Activation Date, Service Commitment, **term end**, contract reference, monthly run-rate, "+" Optimized flag | Inventory |
| 3 | **Billed vs contract rates** | For each service, billed rate vs the current amendment rate card vs the proposed new rate. Gaps where the rate card has no row (exhibit missing). | Rate checks |
| 4 | **Benchmarks** | Market reference for each product/speed/country. **[Note]** Public benchmark data is scarce ("very little information in the public domain" [No Jitter](https://www.nojitter.com/telecommunication-technology/there-is-only-one-sure-way-to-get-the-lowest-possible-telecom-prices)). Use competitive quotes or advisor data. Mark the provenance of each benchmark. | External |
| 5 | **Commitment status** | Volume Commitment type and amount, Contract Year dates, Eligible Charges YTD and forecast, projected shortfall × UC %. Achievement-credit tiers: attained / paid / unpaid. | Commitment module |
| 6 | **Term-end and ETF exposure** | For each service: months remaining × MRC × ETF % (default 75%). Co-terming map. Services already out of term, which are exposed to price changes on notice. Auto-renew candidates and opt-out deadlines. | Inventory + contract |
| 7 | **Open disputes and leverage ledger** | Tier A/B filed (status, aging, amount). Credits approved but not posted. Expired-window historical overcharges. Recurring "rate not implemented" items. | Disputes |
| 8 | **Optimisation scenarios** | Disconnect zombies. Right-size bandwidth. MPLS → SD-WAN/DIA migration. Move/upgrade with the ETF offset for Optimized services (§3.5.3.2). Before/after run-rate. | Scenario engine |
| 9 | **Terms ask-list** | See §3.3.3. | Template |
| 10 | **Missing documents** | What Verizon must supply before signing (§3.3.4), with the reason each is needed. | Doc coverage matrix |

#### 3.3.3 Terms to negotiate (ask-list)

1. **Dispute window** of 12–24 months from invoice date, and delete "Verizon's determination of Disputed Amounts is final" (EMEA §7.4).
2. **Back-billing limit**: no charges more than 3–6 months after accrual. Today it is credit-on-request, not automatic.
3. **Volume Commitment**: lower it to around 70–80% of forecast spend. Advisors note many MPLS deals require "roughly 70% to 80% of actual usage" ([TechTarget](https://www.techtarget.com/searchnetworking/tip/4-steps-to-start-a-successful-migration-from-MPLS-to-SD-WAN)). Also ask for **one aggregate commitment rather than per-service sub-minimums** ([Network World](https://www.networkworld.com/article/719721/lan-wan-top-10-telecom-contract-mistakes.html)), and a **business-downturn / divestiture / restructuring** adjustment clause ([example contract](https://www.cityofflint.com/wp-content/public/2011/2012EM310.PDF)). Ask for a UC % below 75%.
4. **ETF**: lower the % and add a **technology-migration / upgrade waiver** (e.g., MPLS → SD-WAN within Verizon) ([No Jitter](https://www.nojitter.com/digital-workplace/managing-your-communications-carrier-contracts-while-transitioning-to-new-technology)). Add **site-closure** portability.
5. **Rate-card completeness**: every product in use has a rate row, including Managed WAN, Internet Dedicated, SD-WAN and DNM. Add **most-favoured / technology refresh** price reviews every 12 months.
6. **Auto-renewal**: remove it, or make it month-to-month at the same rates. Remove the 10% opt-out uplift (§2.10.2.2). Require **written notice by email to named contacts**, not only a VEC form.
7. **Post-term pricing**: no increase for X months after the term ends (overrides §2.1).
8. **Online terms freeze**: changes to online Master/Service Terms (US §17.14, effective on 15 days' posting) do not apply to existing services without written consent.
9. **Achievement credits**: define the measurement base, payment timing and **no withholding** for unrelated disputes.
10. **Billing deliverables as contractual obligations**: EDI 811 / EDIFACT / VZ450 feed for all BANs. The contract or service reference printed on every invoice line. A monthly inventory report. A single consolidated invoice per country where possible.
11. **Settlement of the open-dispute and leverage ledger** as a signing credit.
12. **SLA credit automation**: proactive credits without a claim requirement.

#### 3.3.4 **Document and data request list to send to Verizon before renewal**

Send it through the Verizon account team (Client Business Manager / Account Manager) in writing, with a deadline. Each item says why it is needed.

**A. Contract corpus**
1. **Fully executed master agreement** and **all numbered amendments** (1…latest), each with its effective date, signature page and pricing attachments. Also a **written confirmation of which amendments are currently in force** and which superseded which.
2. **Every rate exhibit / pricing attachment** for each product in use: Private IP/MPLS ports, access (by country and speed), Internet Dedicated, SD-WAN, Managed WAN tiers, Dynamic Network Manager, CPE/maintenance, voice. **The rate card with the row applied to each active service**, if Verizon can produce it.
3. **All SOFs / NSS orders / MACD orders** for every active service, plus disconnect orders for services cancelled in the audit period.
4. The **versions of online Master Terms and Service Attachments** that the agreement incorporates (by URL and date). Verizon may change online terms "effective upon 15 days posting" (US §17.14).
5. Any **side letters, promotions or credit letters** (signing credits, achievement credits, migration credits).

**B. Inventory and terms**
6. **Full service/circuit inventory** for every BAN: service ID, circuit ID, product, speed, access type and provider, site address, **Activation Date, Service Commitment length, term end date**, contract/amendment and SOF reference, current MRC, Optimized (+) flag. In VEC: Service inventory reports (Access Detail, Service Detail, Managed Service Details, PVC-EVC Details) as CSV ([VEC](https://www.verizon.com/business/support/vec/service-management/view-inventory/)).
7. **List of services past their Service Commitment** (month-to-month) and any **auto-renewed** services, with the renewal dates.
8. **Third-party / local access** services billed through Verizon, with the underlying provider and term.

**C. Commitments and credits**
9. **Volume Commitment statement**: commitment type (AVC/TVC/Tiered/Subminimum), amount, **Contract Year** dates, **Eligible Charges** attributed per Contract Year to date, and Verizon's projected shortfall if any.
10. **Achievement/attainment credit statement**: tiers, measurement period, attainment per period, credits earned, credits paid (with invoice reference), credits withheld and why.
11. **ETF quote**: Verizon's calculation of the early termination exposure per service and in total as of a stated date.

**D. Billing and disputes**
12. **Billing account hierarchy**: every BAN / invoice account, country, currency, legal entity, biller system (e.g., PRIME Biller Next Gen vs Legacy), bill cycle.
13. **Electronic billing enablement** for every BAN: EDI 811, EDIFACT INVOIC or VZ450 direct data, plus IDR/CDR. Also implementation guides and test files ([VEC eMedia](https://www.verizon.com/business/support/vec/billing/electronic-billing-emedia/)). Also: is the client paying a **paper invoice fee**?
14. **Dispute and credit history** for 24–36 months: every inquiry/claim number, date filed, amount, outcome, credit amount, invoice on which the credit posted.
15. **Account payment history and any late-fee / interest charges** with the related invoices.
16. **Tax**: exemption certificates on file per entity/country. GST registration mapping (India: GSTIN of supplier and recipient, place of supply). Italy: SDI XML for every invoice and credit note (TD01/TD04).
17. **FX policy** for non-USD invoices (if contract pricing is USD and billing is local currency): which rate, which date.
18. **Surcharge and fee schedule** applied per BAN (e.g., Carrier Cost Recovery Charge, FUSF for US) with the current rates.

**E. Service quality (for leverage)**
19. **SLA performance reports and SLA credits** for 12–24 months (availability, latency, time to repair) per site.
20. **Open orders / pending disconnects** and their requested vs actual dates.

**F. Commercial proposal**
21. **Renewal proposal** with a **line-item rate card for every active service**, the new commitment, term, ETF and auto-renewal terms. Ask for it in machine-readable form (CSV/XLSX) as well as PDF.

---

## 4. UX/UI best practices for TEM dashboards and audit workbenches

### 4.1 Roles and their jobs

| Role | Primary questions | Primary screens |
|---|---|---|
| **Telecom manager** | What do we have, what is it costing, what is wrong, what expires next? | Inventory, Exceptions, Renewal tracker |
| **TEM analyst / auditor** | Is this finding real? What's the evidence? File it. | Audit workbench, Dispute tracker |
| **AP** | Can I pay this invoice? What do I withhold? By when? | Invoice queue (approve/hold), Payment file |
| **Finance / FP&A** | Spend by entity, cost centre, FY. Accruals. Savings realised. | Spend overview, Allocation, Savings ledger |
| **Procurement** | Commitment attainment, ETF exposure, benchmark, negotiation status | Contract repository, Renewal tracker |
| **Executive sponsor** | Are we being overbilled, how much have we recovered, are we ready for renewal? | One-page summary |

### 4.2 Screen inventory and layout recommendations

**1. Spend overview (home)**
- KPI strip (≤6 tiles): run-rate (MRC) this month vs 12-month average; YTD spend vs budget/FY; **Recoverable (Tier A) open**; **Credits realised YTD**; disputes past SLA; services expiring in ≤90 days.
- Main chart: monthly stacked bars by service family (12–36 months) with a toggle for country/BAN. Second chart: top 10 sites by MRC.
- Each tile drills into a filtered list. No dead-end charts.

**2. Invoice queue**
- One row per invoice with these columns: BAN, country, invoice no., date, due date, total, currency, **extraction status (OK/PARTIAL/FAILED)**, **reconciled Δ (should be 0.00)**, exceptions count by tier, disputed amount, **withhold-by date**, approval state.
- Bulk actions: approve, hold, export AP file.
- This is P360's biggest weakness, so make the **extraction coverage** visible here: a status chip per invoice, and a "why not reconciled" tooltip.

**3. Audit workbench (exception triage)** is the most important screen.
- **Left pane, queue:** grouped by *service × issue*, not by invoice line, so 12 months of the same rate error appear as one item. Sort by recoverable value × urgency (days left in the dispute window). Filters: tier, reason code, BAN, country, product, window remaining, owner.
- **Centre pane, evidence side by side:**
  - left: the **invoice page image** with the line highlighted, plus the parsed values
  - right: the **contract page image** (amendment rate table / SOF) with the applied row highlighted, plus the rate-resolution trace ("SOF #… has no price → Amendment N, table T, row R; rejected rows: …")
  - beneath: a **month-by-month ledger** for the service (billed, expected, prorated days, credits, delta), with sparkline.
- **Right pane, decision:** tier (editable, with mandatory reason), confidence explanation, dispute window countdown, buttons *Confirm → Dispute*, *Not an error (reason)*, *Request document*, *Commercial (move to renewal)*. Every action writes to the audit trail.
- Keyboard-first triage (J/K to move, C confirm, R reject). Show "similar items" so analysts can bulk-confirm the same pattern across services.

**4. Dispute tracker**
- Kanban or table by state (§3.1.2). Columns: carrier ref, filed date, age, amount, approved, **posted**, outstanding, next action and owner.
- Aging buckets 0–30/31–60/61–90/90+. Calero tracks "open versus closed claims, recovered versus denied amounts, and dispute aging" ([Calero](https://www.calero.com/telecom-auditing)).
- Win rate and realisation rate trend. Recommended carrier-follow-up cadence.

**5. Inventory**
- Table + map. Columns: service/circuit ID, site, product, speed, access, BAN, contract ref, Activation, **term end**, MRC (billed vs contract), status (active / disconnect pending / zombie suspect / unbilled).
- Each service page shows its timeline: order → activation → MACDs → invoices → disputes.

**6. Contract repository**
- Document tree (master → amendments → exhibits → SOFs). Per document: type, number, effective date, signed?, superseded-by, **extraction status**, verified-rows % and **coverage** (services that resolve to it).
- Rate-card viewer with filters and the page image beside it.
- A **missing-documents** panel that feeds the carrier request list.

**7. Renewal tracker**
- Countdown to agreement end and notice deadlines.
- Commitment attainment gauge (Eligible Charges YTD vs commitment, with forecast band). ETF exposure by month. Expiry heat-map by quarter.
- Negotiation checklist (§3.3.3) with status. Generates the renewal pack (PDF/XLSX).

### 4.3 Evidence presentation principles

1. **Never show a dollar finding without its two citations** (invoice page and contract page). If either is missing, the finding cannot be above Tier B.
2. **Show the calculation, not just the delta**: rate × days ÷ period − credits = expected.
3. **Separate "money we can claim" from "money at risk"** visually. Tier A/B are green claim value. C is amber, commercial. D is grey, exposure. E is blue, missing info. Never sum them into one "savings" number, which is exactly the P360 failure mode.
4. **Show provenance and confidence** on every extracted number (parser, OCR, LLM, human-verified) with the parser version.
5. **Dispute window first**: the countdown sits next to the amount.
6. **Explain no-finding too**: an "OK" service shows "billed = contract rate (row R)". Showing why a service is clean builds trust.

### 4.4 KPIs (with definitions)

| KPI | Formula | Why |
|---|---|---|
| Extraction coverage | invoices reconciled to the cent ÷ invoices received | Core trust metric. Beats P360 directly. |
| Contract coverage | services with a resolved, verified rate ÷ active services | Drives the Tier E backlog |
| Spend under management | Σ spend on reconciled invoices | Standard industry scope metric **[definition: practitioner]** |
| Recoverable identified (A) / pending confirmation (B) | Σ by tier | Pipeline |
| Credits realised | Σ credits posted on invoices | Hard-money recovery |
| Realisation rate | credits posted ÷ amount disputed (closed) | Quality of claims |
| Dispute win rate | approved+partial ÷ closed | Benchmarked 71%→94% at one enterprise ([No Jitter](https://www.nojitter.com/telecommunication-technology/8-metrics-for-tem)) |
| Dispute aging | median days filed→posted, and the bucket distribution | Carrier responsiveness |
| Window-expired value | Σ findings that passed their window unfiled | Should trend to zero |
| Late fees paid | Σ late fees | Bad AP process ([No Jitter](https://www.nojitter.com/telecommunication-technology/8-metrics-for-tem)) |
| Invoice processing time | received → approved (days) | AP efficiency |
| Run-rate savings | Σ (old MRC − new MRC) for fixed or optimised services | Hard savings |
| Cost avoidance | negotiated-away increases, avoided ETF/UC | Report separately |
| Commitment attainment | Eligible Charges YTD ÷ commitment (and forecast) | Renewal risk |
| ETF exposure | Σ remaining MRC × ETF % | Renewal leverage |

---

## 5. How I would build it in 2026

### 5.1 Target architecture

```
                        ┌────────────────────────── Document store (immutable, hashed) ──────────────────────────┐
Sources                 │ PDFs, scans, EDI 811/EDIFACT/VZ450, SDI XML, CSV inventories, emails                     │
 VEC download / email ─►│ md5 → doc_id; classification (invoice/credit note/statement/SOF/amendment/exhibit/other) │
 EDI/SFTP / upload     └──────────────┬──────────────────────────────────────────────────────────────────────────┘
                                      ▼
                     ┌──── Extraction layer (two independent reads) ────┐
                     │ A. Deterministic: text layer (pdftotext) +        │
                     │    per-layout parsers (VZ_INTL_*, US stmt, GST,   │
                     │    Italy XML, EDI mappers)                        │
                     │ B. OCR (e.g., Mistral OCR batch) → markdown →     │
                     │    LLM extraction with JSON schema (§6.1)         │
                     │ Arbiter: field-level agreement; header reconcile  │
                     │ to the cent; disagreement → human queue            │
                     └──────────────┬───────────────────────────────────┘
                                    ▼
          ┌──── Canonical store (Postgres) ─────────────────────────────────────────────┐
          │ Vendor, Account(BAN), Invoice, InvoiceLine, Service, Site, Contract graph,  │
          │ RateLine, Commitment, Dispute, Credit, GLAllocation, Evidence, AuditEvent  │
          └──────────────┬──────────────────────────────────────────────────────────────┘
                         ▼
   ┌── Contract knowledge graph ──┐   ┌──── Rule engine (deterministic, versioned) ────┐
   │ Master→Amendment→Exhibit→    │──►│ resolve(service, date) → RateLine + trace       │
   │ RateLine; SOF→Service;       │   │ ledger(service, month) → billed/expected/credits │
   │ precedence & effective dates │   │ rules R1…X1 → Finding{tier, reason, evidence}    │
   └──────────────────────────────┘   └──────────────┬──────────────────────────────────┘
                                                     ▼
                   Human-in-the-loop: verification queues (extraction, rate rows, B→A)
                                                     ▼
                Workbench UI ▸ Dispute workflow ▸ Renewal pack generator ▸ Exports (AP/GL/XLSX/PDF)
                                                     ▼
                 LLM services (narrow, schema-bound): claim drafting, explanations, Q&A over SQL views
```

**Design principles:**
1. **LLMs extract and explain. Deterministic code decides.** No LLM ever computes a delta or assigns a tier. LLM outputs are JSON validated against a schema. Every number must be traceable to a page and bbox or a text span.
2. **Two independent reads + reconciliation** is the quality gate. An invoice is "OK" only if the extracted lines plus taxes equal the header total to the cent. Disagreement between read A and read B goes to human review.
3. **Everything is versioned**: parser version, rule version, rate row version, Master Terms version. Findings store the versions that produced them, so a re-run can explain any difference. This matches "Tier A must stay at its audited value unless a change is explained".
4. **Event-sourced audit trail**: every status change, tier override and verification stores who, when, why, and the before and after values.
5. **Idempotent batch pipeline first, real-time later.** Monthly telecom billing doesn't need streaming.
6. **Data residency and PII**: invoices contain site addresses and names. Keep client data out of git (already enforced) and encrypt at rest. Gartner lists GDPR compliance as a selection factor.

### 5.2 Core data model

```sql
vendor(id, name, parent_id)                                  -- Verizon Business, Verizon India, Verizon Italia…
legal_entity(id, name, country, tax_id)                      -- client entities (GSTIN, VAT no.)
site(id, code, name, address, country, legal_entity_id, cost_center)
account(id, vendor_id, ban, country, currency, biller_system, bill_cycle_day, legal_entity_id)

document(id, md5, type, source, received_at, pages, text_layer bool, ocr_status, parser, parser_version)
invoice(id, account_id, document_id, invoice_no, invoice_date, due_date, period_start, period_end,
        currency, total_charges, total_taxes, total_credits, amount_due, doc_kind -- invoice|credit_note|statement
        , extraction_status -- OK|PARTIAL|FAILED
        , reconcile_delta numeric)                           -- must be 0.00 for OK
invoice_line(id, invoice_id, page, bbox, raw_text, service_ref_raw, contract_ref_raw,
             charge_type -- MRC|NRC|NRC_INSTALMENT|USAGE|OCC|CREDIT|TAX|SURCHARGE|PASS_THROUGH|ETF|UC|LATE_FEE
             , description, period_start, period_end, quantity, unit_rate, amount, currency, tax_code,
             service_id NULL, read_a_amount, read_b_amount, agreement -- MATCH|MISMATCH|SINGLE
)

service(id, account_id, site_id, circuit_id, service_id_ext, product, speed, access_type, access_provider,
        optimized bool, status, activation_date, disconnect_date, service_commitment_months,
        term_end_date GENERATED, sof_id NULL, contract_id NULL)
service_dependency(parent_service_id, child_service_id, kind) -- port↔access, SD-WAN↔underlay

contract(id, vendor_id, number, kind -- MASTER|AMENDMENT|EXHIBIT|SOF|NSS|MACD|SIDE_LETTER|ONLINE_TERMS
         , parent_id, amendment_no, effective_date, end_date, signed bool, supersedes_id,
         document_id, precedence_rank, status -- EXTRACTED|VERIFIED)
contract_term(id, contract_id, key -- dispute_window|withhold_window|etf_pct|uc_pct|auto_renew|price_change_notice|fx_clause|back_bill_limit|precedence
              , value_json, page, clause_ref, verified_by, verified_at)
rate_card(id, contract_id, name, currency, effective_from, effective_to, page_start, page_end)
rate_line(id, rate_card_id, product, country, speed, access_type, term_months, charge_type,
          unit, amount, currency, conditions_json, page, table_ref, row_ref, status, verified_by)

commitment(id, contract_id, kind -- AVC|TVC|TIERED|SUBMIN
           , amount, currency, period_start, period_end, contract_year_start, uc_pct, eligible_rules_json)
achievement_tier(id, commitment_id, threshold, credit_pct, measurement_window, scope_json)
commitment_attainment(commitment_id, contract_year, eligible_charges, forecast, as_of)

ledger(service_id, month, billed_mrc, billed_occ, credits, nrc_cum, usage, taxes, pass_through,
       expected_mrc, prorate_days, rate_line_id, delta, computed_by_version)
finding(id, service_id, months int4range, reason_code, tier -- A|B|C|D|E|OK
        , amount, currency, rate_line_id, evidence_json, rule_version, window_deadline, status, owner)
dispute(id, account_id, carrier_ref, filed_at, channel, state, amount_claimed, amount_approved,
        amount_posted, window_basis_term_id, next_action_at)
dispute_finding(dispute_id, finding_id)
credit(id, invoice_line_id, dispute_id NULL, amount, kind -- DISPUTE|SLA|ACHIEVEMENT|PROMO|OTHER)
gl_allocation(id, invoice_line_id, legal_entity_id, cost_center, gl_account, pct, amount)
evidence(id, kind -- INVOICE_PAGE|CONTRACT_PAGE|CALC|INVENTORY|EMAIL, document_id, page, bbox, note)
audit_event(id, entity, entity_id, action, actor, at, before_json, after_json, reason)
doc_request(id, vendor_id, item_code, description, reason, requested_at, received_document_id, status)
```

Key relations: Account 1–N Invoice 1–N InvoiceLine N–1 Service N–1 Site. Service N–1 Contract(SOF) → Amendment → RateCard → RateLine. Finding N–M Dispute. Credit → InvoiceLine (the posted proof).

### 5.3 Rescue roadmap (renewal next month)

**Week 0 (before the client's go/no-go, week of 2026-10-19).** The client has paused payments. Procurement reviews first, then finance makes the decision. Deliver in this order:
1. **Procurement:** (a) the Verizon document-request list (§3.3.4), filled in with the concrete gaps (missing SOFs and contracts, missing rate exhibits, missing statement periods); (b) the renewal leverage summary: term ends, ETF exposure, commitment and achievement-credit status, out-of-term services, open and expired-window claims; (c) billed rates vs the amendment rate card; (d) the terms ask-list (§3.3.3), with the **dispute-window and auto-renewal clauses found in the client's own agreement**.
2. **Finance:** (a) claims split by tier and by **within / outside the dispute window**, with A and B never summed with C, D or E; (b) a spend baseline by service, country and fiscal year; (c) the extraction coverage matrix showing every invoice reconciled to the cent; (d) the legacy-vs-engine comparison as the explanation for the earlier false positives.
3. **A scorecard against the baseline success criteria** the client was originally promised. These live in the project's Drive workspace and include: ≥99% discrepancy detection on 1,000+ lines, reliable PDF/CSV parsing, configurable rules, categorised exceptions, actionable reports, SSO, a 100% audit trail (source file, field origin, rule triggered, timestamp), sign-off by two business users, and six months of history processed within 40 business days. Mark each one Met, Partial (with a date) or Planned. Items 1 and 2 above and the architecture in §5.1 already meet most of the data criteria. SSO and sign-off are process items.

**Days 0–30: win the renewal, prove accuracy**
1. **Extraction coverage matrix** for every Verizon document (header, lines, reconcile, contract prices, OK/PARTIAL/FAILED). This is the head-to-head proof against P360.
2. **OCR second read** (batch) for scanned SOFs and amendments. Two-read reconciliation on invoices.
3. **Renewal pack v1** (§3.3.2), as XLSX + PDF: spend baseline by service/country/FY, billed vs rate card, term-end and ETF exposure, commitment attainment and achievement-credit qualification, open claims + leverage ledger, missing documents, terms ask-list.
4. **Carrier document request** (§3.3.4) sent in week 1. Received items tracked in `doc_request`.
5. **Tier A dispute batch** filed now, before any windows lapse, each with an evidence pack. Window clocks on every finding.
6. **Read-only workbench** (invoice queue + audit workbench with side-by-side evidence) for the client's telecom manager. It may be a thin UI over the engine outputs.

**Days 31–60: operationalise**
7. Dispute tracker with the state machine, credit-posted matching, and aging.
8. Contract repository with rate-row verification UI. Promote B→A.
9. Inventory reconciliation against the VEC inventory export (zombie, duplicate and dangling detection).
10. GL allocation export and an AP "pay / withhold-by" file.
11. Monthly run: new invoices are auto-ingested, reconciled and audited, and the delta report is emailed.

**Days 61–90: scale and differentiate**
12. EDI 811 / EDIFACT / VZ450 ingestion for BANs where Verizon enables it, replacing PDF parsing.
13. Renewal scenario engine (migrations, disconnects, ETF offsets, commitment sizing).
14. NL Q&A over curated SQL views (read-only, cites rows).
15. Generalise to a second carrier, using the parser-per-layout + canonical model pattern.
16. SOC 2 readiness, SSO, and role-based access.

### 5.4 Anti-patterns P360 fell into, and the fix for each

| Anti-pattern | Symptom | Fix |
|---|---|---|
| **"Missing contract = overbilling"** | Huge false-positive totals | Tier E bucket. Never monetised. Generates a document request. |
| **Line-level comparison** | Proration months, credits and instalments all flagged | Compare per service per month after netting. Proration from dates. |
| **Naive NRC comparison** | Each instalment flagged against the full NRC | Cumulative NRC check vs the SOF cap |
| **Wrong price row** | Rate from the wrong speed, country or term | Dimensional key match + resolution trace + human-verified rows only for Tier A |
| **No header reconciliation** | Silent dropped or duplicated lines | Reconcile to the cent or mark FAILED. Two independent reads. |
| **One "savings" number** | Mixes recoverable, commercial, underbilled and unknown | Tiers A–E, never summed. Realised vs identified. |
| **Ignoring contract hierarchy and effective dates** | Old rates applied after an amendment | Effective-date resolver per precedence clause |
| **ETFs and pass-throughs treated as overbilling** | Commercial items in the claim total | Separate C bucket and pass-through bucket |
| **No evidence links** | Carrier rejects, client distrusts | Invoice page + contract page on every claim |
| **No dispute clock** | Claims expire | Window deadlines from contract terms, alerts at T-30/T-7 |
| **Opaque AI** | Unexplainable numbers | LLM only for extraction and drafting, schema-validated. Deterministic rules decide. |
| **UI organised by invoice, not service** | Same error 12× | Group by service × issue |

---

## 6. Ready-to-use prompts (system + task, with JSON schemas)

General conventions for all agents:
- Temperature 0. Use structured output / JSON mode with the schema below, and validate it. Re-ask once on schema failure, then route to human review.
- **The model never invents a number.** Any value not literally present in the input is `null`, with an entry in `issues[]`.
- Every extracted value carries a `source` pointer: page + verbatim snippet.
- Amounts are strings with exactly the decimals printed (avoid float drift). Normalise in code.

### 6.1 Invoice line extraction from OCR markdown, with header reconciliation

**System prompt**
```
You are a telecom invoice extraction engine. You convert ONE carrier invoice (OCR markdown, page-delimited
with "<!-- page N -->" markers) into strict JSON matching the provided schema. You are precise and literal.

Rules:
1. Extract only what is printed. Never infer, compute, or "fix" an amount. If a value is not printed, use null
   and add an issue.
2. Copy amounts exactly as printed (keep sign, thousands separators removed, decimal point normalised to ".";
   a trailing "-" or "CR" or parentheses means negative). Keep the printed currency.
3. Capture the header: vendor, account/BAN and every other reference number with its label, invoice number,
   invoice date, due date, billing period, currency, previous balance, payments, adjustments, current
   charges, taxes, total/amount due. Record each with its page and a verbatim snippet (≤120 chars).
4. Capture EVERY charge line from detail sections (not summary sections), including credits, adjustments,
   instalments, taxes and surcharges. For each line record: page, section heading, verbatim description,
   any service/circuit ID, any contract/agreement/service reference printed near the line (look for tokens
   wrapped across lines such as "(SID/contract)"), site/location, period from/to, quantity, unit rate,
   amount, tax code/rate, and charge_type from the enum.
5. Do NOT include subtotal or total rows as lines; record them in "subtotals" with their label so the
   reconciliation can use them.
6. Classify charge_type conservatively; use "UNKNOWN" if unsure. Tag "ONE_TIME_INSTALMENT" only if the text
   says instalment/installment/"x of y".
7. Language: invoices may be English, Italian or Indian GST format. Map Italian labels (e.g., "Imponibile",
   "IVA", "Totale documento", "Nota di credito") and GST labels (GSTIN, SAC/HSN, CGST/SGST/IGST, Place of
   Supply) into the schema fields; keep originals in "label".
8. Reconciliation: you do NOT compute it. Set reconciliation.claimed_by_model = false. Code will compute it.
9. If pages are missing, garbled, or a table is cut, list it in issues with the page number.
Output JSON only.
```

**Task prompt**
```
Document id: {{doc_id}}   Expected vendor: {{vendor_hint}}   Known layout: {{layout_hint|"unknown"}}
Known BANs for this client: {{ban_list}}
Extract per the schema. OCR markdown follows.
<<<OCR
{{ocr_markdown}}
OCR>>>
```

**Output schema**
```json
{
  "type": "object",
  "required": ["doc_id", "doc_kind", "header", "lines", "subtotals", "issues", "reconciliation"],
  "properties": {
    "doc_id": {"type": "string"},
    "doc_kind": {"enum": ["INVOICE", "CREDIT_NOTE", "STATEMENT", "DEBIT_NOTE", "OTHER"]},
    "header": {
      "type": "object",
      "properties": {
        "vendor_name": {"$ref": "#/$defs/sv"},
        "references": {"type": "array", "items": {"type": "object",
          "required": ["label", "value", "source"],
          "properties": {"label": {"type": "string"}, "value": {"type": "string"},
            "kind": {"enum": ["BAN", "INVOICE_NO", "CUSTOMER_NO", "CONTRACT", "PO", "GSTIN_SUPPLIER", "GSTIN_RECIPIENT", "VAT_NO", "OTHER"]},
            "source": {"$ref": "#/$defs/src"}}}},
        "invoice_date": {"$ref": "#/$defs/sv"}, "due_date": {"$ref": "#/$defs/sv"},
        "period_start": {"$ref": "#/$defs/sv"}, "period_end": {"$ref": "#/$defs/sv"},
        "currency": {"$ref": "#/$defs/sv"},
        "previous_balance": {"$ref": "#/$defs/sv"}, "payments": {"$ref": "#/$defs/sv"},
        "adjustments": {"$ref": "#/$defs/sv"}, "current_charges": {"$ref": "#/$defs/sv"},
        "total_taxes": {"$ref": "#/$defs/sv"}, "total_due": {"$ref": "#/$defs/sv"},
        "place_of_supply": {"$ref": "#/$defs/sv"}
      }
    },
    "lines": {"type": "array", "items": {"type": "object",
      "required": ["line_no", "description", "amount", "charge_type", "source"],
      "properties": {
        "line_no": {"type": "integer"},
        "section": {"type": ["string", "null"]},
        "description": {"type": "string"},
        "service_ref": {"type": ["string", "null"]},
        "contract_ref": {"type": ["string", "null"]},
        "site": {"type": ["string", "null"]},
        "period_start": {"type": ["string", "null"], "description": "ISO date"},
        "period_end": {"type": ["string", "null"]},
        "quantity": {"type": ["string", "null"]},
        "unit_rate": {"type": ["string", "null"]},
        "amount": {"type": "string", "pattern": "^-?[0-9]+(\\.[0-9]+)?$"},
        "currency": {"type": ["string", "null"]},
        "tax_code": {"type": ["string", "null"]}, "tax_rate": {"type": ["string", "null"]},
        "charge_type": {"enum": ["MRC", "NRC", "ONE_TIME_INSTALMENT", "USAGE", "OCC", "CREDIT", "TAX", "SURCHARGE", "PASS_THROUGH", "ETF", "UNDERUTILIZATION", "LATE_FEE", "FX_ADJ", "UNKNOWN"]},
        "source": {"$ref": "#/$defs/src"}
      }}},
    "subtotals": {"type": "array", "items": {"type": "object",
      "properties": {"label": {"type": "string"}, "scope": {"type": "string"}, "amount": {"type": "string"}, "source": {"$ref": "#/$defs/src"}}}},
    "reconciliation": {"type": "object", "properties": {"claimed_by_model": {"const": false}}},
    "issues": {"type": "array", "items": {"type": "object",
      "properties": {"page": {"type": ["integer", "null"]}, "severity": {"enum": ["INFO", "WARN", "BLOCKER"]}, "message": {"type": "string"}}}}
  },
  "$defs": {
    "src": {"type": "object", "required": ["page", "snippet"], "properties": {"page": {"type": "integer"}, "snippet": {"type": "string", "maxLength": 160}}},
    "sv": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"]}, "label": {"type": ["string", "null"]}, "source": {"$ref": "#/$defs/src"}}}
  }
}
```

**Post-processing (code, not LLM):** Σ(lines excluding TAX) + Σ(TAX) ± adjustments = current_charges, then reconcile to total_due with balance-forward items. A delta ≠ 0.00 means FAILED, and a subtotal-level diff localises the gap. Compare line by line against the deterministic parser (read A). Any MISMATCH goes to human review.

### 6.2 Contract / SOF / amendment abstraction into a rate schema

**System prompt**
```
You are a telecom contract abstraction specialist (carrier master agreements, numbered amendments, pricing
attachments/rate exhibits, Service Order Forms). You convert ONE document (OCR markdown with page markers)
into structured JSON for a billing-audit rate engine.

Rules:
1. Identify the document: type (MASTER, AMENDMENT, PRICING_EXHIBIT, SOF, NSS, MACD_ORDER, SIDE_LETTER,
   SERVICE_TERMS, OTHER), contract/agreement number, amendment number, effective date, term, signature
   status (signed by both parties? names/dates visible?), and which prior documents it amends/supersedes
   (quote the clause).
2. Extract every price table row as a separate rate_line with ALL dimensions present in the table: product,
   service variant, country/region/city, port or access speed (normalise to Mbps but keep raw), access type
   (e.g., Ethernet, MPLS port, DIA, broadband, managed tier), term (months), charge type (MRC/NRC/usage/
   per-unit), unit, currency, amount, and any condition text (e.g., "with 36-month term", "waived if…").
   Record page, table title, and row label verbatim. Never merge rows. Never compute values.
3. Extract commercial terms with verbatim quotes and page: volume/revenue commitment (type, amount, period,
   contract year start, eligible-charges definition, shortfall %), achievement/attainment credit tiers,
   service commitment/term, early termination %, auto-renewal and notice, price change rights, dispute
   window and withholding window, back-billing limit, order-of-precedence clause, FX/currency clause,
   SLA credit terms, migration/technology-upgrade waivers, business downturn clause.
4. For an SOF: also extract site address, circuit/service IDs, product, speed, access, Service Commitment,
   each price (MRC/NRC/instalments), ICB indicators, requested/committed dates.
5. If a value is illegible or absent, use null and add an issue. If text looks like an unsigned draft or a
   quote rather than an executed contract, set signed=false and flag it.
6. Output JSON only, matching the schema.
```

**Task prompt**
```
Document id: {{doc_id}}  Filename: {{filename}}  Client legal entities: {{entities}}
Known contract numbers so far: {{known_contracts}}
Abstract this document per the schema.
<<<OCR
{{ocr_markdown}}
OCR>>>
```

**Output schema**
```json
{
  "type": "object",
  "required": ["doc_id", "doc_type", "identity", "rate_lines", "terms", "sof", "issues"],
  "properties": {
    "doc_id": {"type": "string"},
    "doc_type": {"enum": ["MASTER", "AMENDMENT", "PRICING_EXHIBIT", "SOF", "NSS", "MACD_ORDER", "SIDE_LETTER", "SERVICE_TERMS", "OTHER"]},
    "identity": {"type": "object", "properties": {
      "contract_number": {"type": ["string", "null"]},
      "amendment_number": {"type": ["string", "null"]},
      "effective_date": {"type": ["string", "null"]},
      "end_date": {"type": ["string", "null"]},
      "signed": {"type": ["boolean", "null"]},
      "signatories": {"type": "array", "items": {"type": "string"}},
      "amends_or_supersedes": {"type": "array", "items": {"type": "object", "properties": {
        "reference": {"type": "string"}, "quote": {"type": "string"}, "page": {"type": "integer"}}}},
      "source": {"$ref": "#/$defs/src"}}},
    "rate_lines": {"type": "array", "items": {"type": "object",
      "required": ["product", "charge_type", "amount", "currency", "source"],
      "properties": {
        "product": {"type": "string"}, "variant": {"type": ["string", "null"]},
        "country": {"type": ["string", "null"]}, "region": {"type": ["string", "null"]}, "city": {"type": ["string", "null"]},
        "speed_raw": {"type": ["string", "null"]}, "speed_mbps": {"type": ["number", "null"]},
        "access_type": {"type": ["string", "null"]},
        "term_months": {"type": ["integer", "null"]},
        "charge_type": {"enum": ["MRC", "NRC", "USAGE", "PER_UNIT", "DISCOUNT_PCT", "OTHER"]},
        "unit": {"type": ["string", "null"]},
        "amount": {"type": "string"}, "currency": {"type": "string"},
        "conditions": {"type": ["string", "null"]},
        "table_title": {"type": ["string", "null"]}, "row_label": {"type": ["string", "null"]},
        "source": {"$ref": "#/$defs/src"}}}},
    "terms": {"type": "array", "items": {"type": "object",
      "required": ["key", "quote", "source"],
      "properties": {
        "key": {"enum": ["VOLUME_COMMITMENT", "ACHIEVEMENT_CREDIT_TIER", "SERVICE_COMMITMENT", "ETF", "UNDERUTILIZATION_PCT", "AUTO_RENEWAL", "PRICE_CHANGE", "DISPUTE_WINDOW", "WITHHOLD_WINDOW", "BACK_BILLING_LIMIT", "ORDER_OF_PRECEDENCE", "FX_CLAUSE", "SLA_CREDIT", "MIGRATION_WAIVER", "BUSINESS_DOWNTURN", "ELIGIBLE_CHARGES_DEF", "CONTRACT_YEAR", "OTHER"]},
        "value": {"type": "object", "description": "normalised fields, e.g. {amount, currency, period_months, pct, days, basis:'INVOICE_DATE'|'DUE_DATE'}"},
        "quote": {"type": "string", "maxLength": 600},
        "source": {"$ref": "#/$defs/src"}}}},
    "sof": {"type": ["object", "null"], "properties": {
      "sof_number": {"type": ["string", "null"]}, "site_address": {"type": ["string", "null"]},
      "services": {"type": "array", "items": {"type": "object", "properties": {
        "circuit_or_service_id": {"type": ["string", "null"]}, "product": {"type": "string"},
        "speed_raw": {"type": ["string", "null"]}, "access_type": {"type": ["string", "null"]},
        "service_commitment_months": {"type": ["integer", "null"]},
        "mrc": {"type": ["string", "null"]}, "nrc": {"type": ["string", "null"]},
        "nrc_instalments": {"type": ["integer", "null"]}, "currency": {"type": ["string", "null"]},
        "icb": {"type": ["boolean", "null"]}, "source": {"$ref": "#/$defs/src"}}}}}},
    "issues": {"type": "array", "items": {"type": "object", "properties": {
      "page": {"type": ["integer", "null"]}, "severity": {"enum": ["INFO", "WARN", "BLOCKER"]}, "message": {"type": "string"}}}}
  },
  "$defs": {"src": {"type": "object", "required": ["page"], "properties": {"page": {"type": "integer"}, "snippet": {"type": "string", "maxLength": 200}}}}
}
```

Every `rate_line` lands as `EXTRACTED`. Only a human-verified row (side-by-side with the page image) becomes `VERIFIED` and can support Tier A.

### 6.3 Discrepancy explanation and claim drafting, with citations

**System prompt**
```
You draft billing dispute claims to a telecom carrier on behalf of an enterprise customer. You receive a
structured FINDING produced by a deterministic audit engine (amounts already computed and verified), with
evidence pointers. Your job is wording, not arithmetic.

Rules:
1. Use ONLY facts in the FINDING. Do not recalculate, round differently, or add amounts. Copy every number
   exactly, with currency.
2. Every factual sentence about the contract or invoice must carry a citation tag in the form
   [INV:{invoice_no} p.{page}] or [CTR:{document} p.{page} {table/row or clause}].
3. Tone: factual, courteous, firm. No accusations, no speculation about intent, no legal threats.
4. Structure: subject line; account and invoice identifiers; one-paragraph summary; table of affected
   invoices (invoice no., date, billed, contractual, difference); contractual basis (quote ≤ 40 words);
   calculation method (proration, netting) in one or two sentences; requested remedy (credit amount per
   invoice AND correction of the rate going forward; late-fee reversal if listed); timeliness statement
   citing the dispute-window clause and filing date; attachments list.
5. If tier is not A, or evidence is missing for any invoice, or window_status is EXPIRED, do NOT draft a
   claim: return status "NOT_DRAFTED" with the reason (expired items go to the renewal leverage ledger).
6. Also produce a 2–3 sentence plain-English explanation for the internal workbench.
Output JSON only.
```

**Task prompt**
```
FINDING:
{{finding_json}}
Customer legal entity: {{entity}}   Carrier: {{carrier}}   Channel: {{channel e.g. "VEC billing inquiry"}}
Filing date: {{today}}
```

**Input (finding) shape:** `{finding_id, tier, reason_code, service:{id, circuit_id, site, product, speed}, account:{ban}, months:[{invoice_no, invoice_date, page, billed, expected, delta, currency, prorate_days}], total_delta, currency, contract:{document, amendment, page, table, row, rate, quote}, window:{clause_quote, clause_page, basis, deadline, status}, late_fees:[...], attachments:[...]}`

**Output schema**
```json
{
  "type": "object",
  "required": ["finding_id", "status", "internal_explanation"],
  "properties": {
    "finding_id": {"type": "string"},
    "status": {"enum": ["DRAFTED", "NOT_DRAFTED"]},
    "not_drafted_reason": {"type": ["string", "null"]},
    "internal_explanation": {"type": "string", "maxLength": 600},
    "claim": {"type": ["object", "null"], "properties": {
      "subject": {"type": "string", "maxLength": 140},
      "body_markdown": {"type": "string"},
      "invoice_table": {"type": "array", "items": {"type": "object", "properties": {
        "invoice_no": {"type": "string"}, "invoice_date": {"type": "string"},
        "billed": {"type": "string"}, "contractual": {"type": "string"}, "difference": {"type": "string"}, "currency": {"type": "string"},
        "citation": {"type": "string"}}}},
      "requested_credit_total": {"type": "string"},
      "forward_correction_requested": {"type": "boolean"},
      "citations": {"type": "array", "items": {"type": "string"}},
      "attachments": {"type": "array", "items": {"type": "string"}}}}
  }
}
```

**Code check after generation:** every number in `body_markdown` must appear in the finding (regex comparison), `requested_credit_total` must equal `total_delta`, and every citation must resolve to an evidence record. Reject the draft on any mismatch.

### 6.4 Renewal pack generation

**System prompt**
```
You are a telecom sourcing advisor preparing a carrier contract renewal negotiation pack for an enterprise.
You receive pre-computed DATA (spend series, inventory with term ends, billed-vs-contract rate comparison,
commitment attainment, ETF exposure, findings by tier, dispute status, missing documents, contract terms).
Your job: organise, prioritise and write the narrative; never compute new numbers.

Rules:
1. Use only numbers present in DATA; reference them by their DATA key (e.g., {{spend.fy_total}}) in a
   "figures_used" list so code can verify them.
2. Keep tiers separate: A/B claims (recoverable), C (commercial), D (underbilled exposure), E (unverifiable),
   expired-window historical overcharges (leverage only). Never add them together.
3. Produce: executive summary (≤150 words); position summary (what we buy, run-rate, where we are over
   contract, where Verizon is out of term); risks (shortfall, ETF, auto-renewal, post-term price changes);
   leverage (open disputes, unimplemented rates, SLA misses, expired-window history); negotiation asks
   ranked by value and likelihood, each tied to evidence; walk-away/BATNA notes; documents to obtain before
   signing; a timeline with notice deadlines.
4. Flag every assumption explicitly (e.g., "benchmark source: competitive quote dated …" or "no benchmark").
5. Output JSON only.
```

**Task prompt**
```
Client: {{client_alias}}  Carrier: {{carrier}}  Agreement end: {{end_date}}  Negotiation date: {{date}}
Fiscal year definition: {{fy_def}}
DATA:
{{renewal_data_json}}
```

**Output schema**
```json
{
  "type": "object",
  "required": ["executive_summary", "sections", "asks", "risks", "documents_needed", "timeline", "figures_used", "assumptions"],
  "properties": {
    "executive_summary": {"type": "string", "maxLength": 1200},
    "sections": {"type": "array", "items": {"type": "object", "properties": {
      "id": {"enum": ["SPEND_BASELINE", "INVENTORY", "RATES_VS_CONTRACT", "BENCHMARKS", "COMMITMENT", "TERM_ETF", "DISPUTES_LEVERAGE", "OPTIMISATION", "TERMS", "MISSING_DOCS"]},
      "title": {"type": "string"}, "narrative_markdown": {"type": "string"},
      "tables": {"type": "array", "items": {"type": "object", "properties": {"data_key": {"type": "string"}, "caption": {"type": "string"}}}}}}},
    "asks": {"type": "array", "items": {"type": "object", "properties": {
      "rank": {"type": "integer"}, "ask": {"type": "string"}, "rationale": {"type": "string"},
      "evidence_keys": {"type": "array", "items": {"type": "string"}},
      "value_key": {"type": ["string", "null"]}, "likelihood": {"enum": ["HIGH", "MEDIUM", "LOW"]},
      "fallback": {"type": ["string", "null"]}}}},
    "risks": {"type": "array", "items": {"type": "object", "properties": {
      "risk": {"type": "string"}, "value_key": {"type": ["string", "null"]}, "mitigation": {"type": "string"}}}},
    "documents_needed": {"type": "array", "items": {"type": "string"}},
    "timeline": {"type": "array", "items": {"type": "object", "properties": {"date": {"type": "string"}, "event": {"type": "string"}}}},
    "figures_used": {"type": "array", "items": {"type": "string"}},
    "assumptions": {"type": "array", "items": {"type": "string"}}
  }
}
```

### 6.5 Carrier document-request list generator

**System prompt**
```
You generate a precise, professional document and data request to a telecom carrier account team, so an
enterprise can audit invoices and prepare a contract renewal. You receive: the client's document inventory
(what we have, with coverage status), the engine's gap list (services with no contract, rate cards with
missing products, invoices failing reconciliation, BANs without e-billing, unknown term ends), and the
carrier name.

Rules:
1. Start from the STANDARD CHECKLIST below; keep only items that are missing or incomplete, and add
   specific items from the gap list (cite the concrete identifiers: BAN, circuit ID, SOF no., amendment no.,
   invoice period). Never ask for something already marked RECEIVED.
2. Each item: id, category, exact request wording, why we need it (one line, business reason), format
   wanted (PDF executed copy / CSV / XLSX / EDI file), scope (identifiers, period), priority (P1 renewal-
   blocking / P2 audit / P3 nice-to-have), and the internal owner who will chase it.
3. Group into a cover email (≤200 words, courteous, with a requested response date) plus the item table.
4. Do not include internal findings, dollar amounts, or accusations in the carrier-facing text.

STANDARD CHECKLIST (codes):
A1 executed master agreement; A2 all amendments + confirmation which are in force; A3 all pricing
attachments / rate exhibits per product; A4 all SOF/NSS/MACD and disconnect orders; A5 incorporated online
terms versions; A6 side letters/promotions/credit letters;
B1 full service inventory with activation, commitment, term end, contract & SOF ref, MRC; B2 out-of-term
and auto-renewed services; B3 third-party/local access details;
C1 volume commitment statement with eligible charges by contract year; C2 achievement credit statement
(earned/paid/withheld); C3 ETF calculation per service;
D1 billing account hierarchy and biller system; D2 EDI 811/EDIFACT/VZ450 enablement + guides + test files;
D3 dispute/credit history 24–36 months; D4 payment and late-fee history; D5 tax exemption/GST/VAT mappings,
e-invoice XML; D6 FX policy; D7 surcharge schedule;
E1 SLA performance and credits; E2 open orders/pending disconnects;
F1 renewal proposal with line-item rate card in CSV/XLSX.
Output JSON only.
```

**Task prompt**
```
Carrier: {{carrier}}  Client alias: {{client_alias}}  Response needed by: {{date}}
Document inventory: {{doc_inventory_json}}
Gap list: {{gap_list_json}}
```

**Output schema**
```json
{
  "type": "object",
  "required": ["cover_email", "items"],
  "properties": {
    "cover_email": {"type": "object", "properties": {"subject": {"type": "string"}, "body": {"type": "string", "maxLength": 1600}}},
    "items": {"type": "array", "items": {"type": "object",
      "required": ["id", "category", "request", "why", "format", "priority"],
      "properties": {
        "id": {"type": "string", "description": "checklist code or G-n for gap-derived"},
        "category": {"enum": ["CONTRACT", "INVENTORY", "COMMITMENT_CREDITS", "BILLING_DISPUTES", "TAX_FX", "SERVICE_QUALITY", "PROPOSAL"]},
        "request": {"type": "string"},
        "why": {"type": "string", "maxLength": 200},
        "format": {"type": "string"},
        "scope": {"type": "object", "properties": {
          "bans": {"type": "array", "items": {"type": "string"}},
          "service_ids": {"type": "array", "items": {"type": "string"}},
          "documents": {"type": "array", "items": {"type": "string"}},
          "period": {"type": ["string", "null"]}}},
        "priority": {"enum": ["P1", "P2", "P3"]},
        "internal_owner": {"type": ["string", "null"]}}}}
  }
}
```

---

## 7. Open questions and verification to-dos

1. **Which dispute and withholding windows does the client's own Verizon agreement set?** The public US, EMEA and online terms differ (§3.1.4). Abstract the clause from the master agreement or amendments and store it as `contract_term(DISPUTE_WINDOW)`.
2. **Which order-of-precedence clause applies?** US USSA (Master Terms > Service Attachments > Pricing; USSA > Orders) and online terms (Service Order > Agreement) differ. This decides SOF vs rate-card conflicts.
3. **Is the auto-renewal clause (§2.10.2.2) in the client's agreement?** It applies only where all services are priced at order and no Volume Commitment exists.
4. **Achievement-credit measurement base and payment evidence.** Read the tiers from the client's amendment. Do not use public promotions.
5. **Which Verizon biller does each international BAN use** (PRIME Next Gen vs Legacy)? This decides which EDIFACT guide applies.
6. **2026 Gartner Market Guide full text** (paywalled). Vendor list and trends beyond the press releases are unverified.
7. **AOTMP standards library content** is member-gated. I found no public lifecycle or error-taxonomy standard.
