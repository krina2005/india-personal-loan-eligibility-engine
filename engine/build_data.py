"""Builds data/*.csv|json from curated records. Every value traces to sources.csv or is UNKNOWN."""
import csv, json, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"); ACC = "2026-10-10"
def w(name, rows, cols):
    with open(f"{D}/{name}", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols); wr.writeheader(); wr.writerows(rows)
S = [
("S01","https://hdfcbank.com/personal/borrow/popular-loans/types-of-personal-loan/personal-loan-for-salaried","personal loan for salaried","HDFC Bank","","OFFICIAL","Salaried product page; age, income, rate, tenure."),
("S02","https://paisabazaar.com/hdfc-bank/personal-loan-eligibility","HDFC personal loan eligibility","Paisabazaar (comparison site)","","SECONDARY","Min credit score 650 claim; also says most lenders cap total EMIs at 50-60% of income."),
("S03","https://www.bankbazaar.com/hdfc-personal-loan-eligibility-calculator.html","HDFC Personal Loan Eligibility","BankBazaar (comparison site)","","SECONDARY","Says up to Rs 40 lakh and 60 months; tenure conflicts with S01 (72)."),
("S04","https://www.bajajfinserv.in/personal-loan-of-5-lakh-for-3-years","Personal Loan of Rs. 5 lakh for 3 years","Bajaj Finance Ltd","","OFFICIAL","Age 21-80 (at end of tenure), CIBIL 685+, tenure 12-96 mo, salary 'Rs 25,001 or more' (snippet partly garbled)."),
("S05","https://www.bajajfinserv.in/personal-loan-salary-less-than-15000","Personal Loan for Salary Less Than 15,000","Bajaj Finance Ltd","2026-08-24 (page meta-tag; semantics unclear)","OFFICIAL","web_fetch returned only site navigation; no eligibility values extracted. Title implies lower salaries may be considered -> unresolved."),
("S06","https://sbi.co.in/web/personal-banking/loans","Loans to Salaried Employees (Xpress Credit)","State Bank of India","","OFFICIAL","Snippet: SBI salary account, up to 30 lakh, min tenure 6 months, close by retirement/60 yrs. Several numeric fields truncated."),
("S07","https://cleartax.in/s/sbi-personal-loan-emi-calculator","SBI personal loan EMI calculator","ClearTax (comparison site)","","SECONDARY","Xpress Credit: min income 15,000; EMI/NMI<50%; CIBIL 750; rate 11.15-14.30; age 21 to <58."),
("S08","https://tatacapital.com/blog/?p=30850","Personal Loan Government Scheme (blog)","Tata Capital blog","","SECONDARY_LOW","Third-party blog on SBI Xpress Credit: 10.65-14.15%, tenure 6 mo-6 yrs. Low quality."),
("S09","https://www.bankbazaar.com/sbi-loan.html","SBI Personal Loan 2026","BankBazaar (comparison site)","","SECONDARY","Says up to Rs 20 lakh, lowest rate 10.30; conflicts with S06/S07/S08."),
("S10","https://cartrade.bankbazaar.com/hdfc-personal-loan-interest-rates.html","HDFC Personal Loan Interest Rates","BankBazaar (comparison site)","","SECONDARY","Says rates from 9.99%; conflicts with S01 (10.90%)."),
("S11","https://www.bajajfinserv.in/35000-salary-personal-loan","35,000 salary personal loan","Bajaj Finance Ltd","","OFFICIAL","Its eligibility calculator uses salary, existing dues and city of residence; no thresholds."),
("M01","https://www.crifhighmark.com/news-events/news/2025/jan/personal-loan-growth-slows-to-138-in-h1fy25-long-term-delinquencies-rise-crif","Personal loan growth slows to 13.8% in H1FY25","CRIF High Mark","2025-01-21","MARKET","Sep-2024 PL portfolio: PSB 37.8%, Pvt banks 32.9%, NBFC 24.1%; NBFCs 68.7% of active loans. Segment-level only."),
("M02","https://jmflresearch.com/JMnew/JMCRM/analystreports/pdf/Consumption%20credit%20landscape.pdf","India Financials - Consumption credit landscape","JM Financial","2025-07-23","MARKET","NBFC/HFCs gaining PL share, private banks losing (CRIF data). No lender ranking in retrieved text."),
("M03","https://www.crifhighmark.com/media/6260/how-india-lends-feb-2026.pdf","How India Lends (Dec 2025)","CRIF High Mark","2026-02","MARKET","NBFCs 91.1% of PL volume, 36.6% of value. No lender-level ranking in retrieved text."),
("M04","https://visionias.in/current-affairs/upsc-daily-news-summary/article/2026-07-01/the-economic-times/economy/fintechs-capture-57-share-of-small-personal-loans-as-stress-mounts-rbi-report","Fintechs capture 57% share of small personal loans (summary of RBI report)","Vision IAS summarising Economic Times","2026-07-01","MARKET_SECONDARY","Fintech 56.8% of PL < Rs 50,000 by Mar-2026 (secondary summary)."),
("M05","https://experian.in/how-fintechs-are-revolutionising-lending","Small is BIG","Experian India","","MARKET","Fintechs ~52% of PL (small-ticket, FY24)."),
("M06","https://assets.equifax.com/marketing/india/assets/disha-retail-insights-june-26.pdf","Retail QBR May 2026","Equifax India","2026-05","MARKET","Segment-level PL growth; lender names not extractable from snippet."),
]
w("sources.csv",[dict(source_id=a,url=b,title=c,publisher=d,date_accessed=ACC,publication_date=e,evidence_quality=f,notes=g) for a,b,c,d,e,f,g in S],
  ["source_id","url","title","publisher","date_accessed","publication_date","evidence_quality","notes"])
L = [
("L01","State Bank of India","SBI","PUBLIC_BANK","Xpress Credit Personal Loan","https://sbi.co.in/web/personal-banking/loans","S06"),
("L02","HDFC Bank Ltd","HDFC Bank","PRIVATE_BANK","Personal Loan (salaried)","https://hdfcbank.com/personal/borrow/popular-loans/types-of-personal-loan/personal-loan-for-salaried","S01"),
("L03","ICICI Bank Ltd","ICICI Bank","PRIVATE_BANK","","",""),("L04","Axis Bank Ltd","Axis Bank","PRIVATE_BANK","","",""),
("L05","Kotak Mahindra Bank Ltd","Kotak Mahindra Bank","PRIVATE_BANK","","",""),("L06","IndusInd Bank Ltd","IndusInd Bank","PRIVATE_BANK","","",""),
("L07","Yes Bank Ltd","Yes Bank","PRIVATE_BANK","","",""),("L08","IDFC FIRST Bank Ltd","IDFC FIRST Bank","PRIVATE_BANK","","",""),
("L09","Federal Bank Ltd","Federal Bank","PRIVATE_BANK","","",""),("L10","Bank of Baroda","Bank of Baroda","PUBLIC_BANK","","",""),
("L11","Punjab National Bank","PNB","PUBLIC_BANK","","",""),("L12","Canara Bank","Canara Bank","PUBLIC_BANK","","",""),
("L13","Bajaj Finance Ltd","Bajaj Finserv","NBFC","Bajaj Finance Personal Loan (Term / Flexi Term / Flexi Hybrid)","https://www.bajajfinserv.in/personal-loan-of-5-lakh-for-3-years","S04"),
("L14","Tata Capital Financial Services Ltd","Tata Capital","NBFC","","",""),("L15","Aditya Birla Finance Ltd","Aditya Birla Capital","NBFC","","",""),
("L16","SMFG India Credit Co Ltd (formerly Fullerton India)","SMFG India Credit","NBFC","","",""),("L17","Hero FinCorp Ltd","Hero FinCorp","NBFC","","",""),
("L18","Poonawalla Fincorp Ltd","Poonawalla Fincorp","NBFC","","",""),("L19","IIFL Finance Ltd","IIFL Finance","NBFC","","",""),
("L20","InCred Financial Services Ltd","InCred","NBFC","","",""),
]
rows=[]
for i,n,b,c,p,u,s in L:
    rows.append(dict(lender_id=i,legal_name=n,brand_name=b,category=c,personal_loan_product=p or "NOT_VERIFIED",product_url=u,
      offers_pl_evidence_status="VERIFIED_OFFICIAL_PAGE" if s else "NOT_VERIFIED_THIS_SESSION",offers_pl_source_id=s,entity_role="ACTUAL_LENDER",
      market_relevance_evidence="Segment-level only (PSB/private bank/NBFC groups are PL-relevant per M01,M03); no lender-level ranking found",
      inclusion_reason="Analyst shortlist spanning PSB/private bank/NBFC segments; NOT a ranked top-20",
      rules_research_depth="PARTIAL" if s else "NONE",selection_source_ids="M01;M02;M03",date_accessed=ACC))
w("lenders.csv",rows,list(rows[0].keys()))
R = [
("L02","min_age","ALL","21","years","VERIFIED_OFFICIAL","S01","Must be between 21 years and 60 years of age",""),
("L02","max_age_application","ALL","60","years","VERIFIED_OFFICIAL","S01","Must be between 21 years and 60 years of age","Page does not say if 60 is at application or maturity; treated as at application (assumption)."),
("L02","min_income","salary_account_holder","25000","INR/month net","VERIFIED_OFFICIAL","S01","HDFC Bank Salary Account holder: minimum net monthly income Rs 25,000",""),
("L02","min_income","non_salary_account","50000","INR/month net","VERIFIED_OFFICIAL","S01","Non-HDFC salary account: minimum net monthly income Rs 50,000",""),
("L02","min_cibil","ALL","650","score","VERIFIED_SECONDARY","S02","HDFC Bank requires a minimum CIBIL Score of 650","Not on retrieved official snippet."),
("L02","employment_scope","ALL","salaried","","VERIFIED_OFFICIAL","S01","Product page is for salaried applicants","Self-employed HDFC product not researched."),
("L02","rate_min","ALL","10.90","% p.a.","VERIFIED_OFFICIAL","S01","10.90% to 24.00% (Fixed Rate)","Conflict: S10 says 9.99%; official preferred. Range, not applicant quote."),
("L02","rate_max","ALL","24.00","% p.a.","VERIFIED_OFFICIAL","S01","10.90% to 24.00% (Fixed Rate)","Fixed rate."),
("L02","tenure_min","ALL","3","months","VERIFIED_OFFICIAL","S01","Tenure 03 Months to 72 Months",""),
("L02","tenure_max","ALL","72","months","VERIFIED_OFFICIAL","S01","Tenure 03 Months to 72 Months","Conflict: S03 says 60; official preferred."),
("L02","amount_max","ALL","4000000","INR","VERIFIED_SECONDARY","S03","up to Rs.40 lakh","Secondary only."),
("L13","min_age","ALL","21","years","VERIFIED_OFFICIAL","S04","Age: 21 years to 80 years*",""),
("L13","max_age_at_maturity","ALL","80","years","VERIFIED_OFFICIAL","S04","You should be 80 years or younger at the end of the loan tenure",""),
("L13","min_cibil","ALL","685","score","VERIFIED_OFFICIAL","S04","CIBIL score: 685 or higher","Repeated across Bajaj pages."),
("L13","min_income","salaried","25001","INR/month","CONFLICTING","S04;S05","S04: 'Rs 25,001 or more to apply'; S05 page titled for salary below 15,000","Unresolved: S05 content not extractable. Engine will not use 25,001."),
("L13","employment_scope","ALL","salaried","","VERIFIED_OFFICIAL","S04","Eligibility lists monthly salary; salary slips requested","Self-employed rules not researched."),
("L13","tenure_min","ALL","12","months","VERIFIED_OFFICIAL","S04","Tenure ranging from 12 months to 96 months",""),
("L13","tenure_max","ALL","96","months","VERIFIED_OFFICIAL","S04","Tenure ranging from 12 months to 96 months",""),
("L13","city_restrictions","ALL","","","OBSERVED_IN_CALCULATOR","S11","Calculator estimates loan using salary, existing dues and city of residence","City matters but cities/thresholds unpublished -> not evaluable."),
("L01","min_age","Xpress Credit","21","years","VERIFIED_SECONDARY","S07","applicant aged about 21 years","'about 21' wording."),
("L01","max_age_at_maturity","Xpress Credit","60","years","VERIFIED_OFFICIAL","S06","Loan to be closed on or before Date of Retirement / End of Contract / 60 years of age","S07 says below 58 at maturity (secondary conflict); official used."),
("L01","min_income","Xpress Credit","15000","INR/month net","VERIFIED_SECONDARY","S07","minimum monthly income should be Rs 15,000","Official figure truncated in snippet."),
("L01","min_cibil","Xpress Credit","750","score","VERIFIED_SECONDARY","S07","minimum CIBIL score should be 750 or above","Secondary only."),
("L01","salary_account_required","Xpress Credit","SBI","bank","VERIFIED_OFFICIAL","S06","Individuals with Salary Account with SBI","Other SBI PL products not researched."),
("L01","employment_scope","ALL","salaried","","VERIFIED_OFFICIAL","S06","Page: Loans to Salaried Employees","Other SBI PL products not researched."),
("L01","emi_nmi_max_ratio","Xpress Credit","0.50","ratio","VERIFIED_SECONDARY","S07","EMI/NMI Ratio should be less than 50%","Secondary only."),
("L01","amount_max","Xpress Credit","3000000","INR","VERIFIED_OFFICIAL","S06","Loan up to 30 lakhs","S09 says 20 lakh (conflict); official preferred."),
("L01","tenure_min","Xpress Credit","6","months","VERIFIED_OFFICIAL","S06","Minimum: 6 months",""),
("L01","tenure_max","Xpress Credit","72","months","VERIFIED_SECONDARY","S08","minimum of six months and a maximum of six years","Low-quality secondary."),
("L01","rate_min","Xpress Credit","","% p.a.","CONFLICTING","S07;S08;S09","S07 11.15-14.30; S08 10.65-14.15; S09 lowest 10.30","No official rate retrieved."),
("L01","rate_max","Xpress Credit","","% p.a.","CONFLICTING","S07;S08","S07 14.30; S08 14.15","As above."),
("L01","prepayment","Xpress Credit","3% on takeover by other banks; none after 3-yr tenure completion","","VERIFIED_OFFICIAL","S06","pre-payment penalty of 3% ... takeover cases","Snippet wording; rest truncated."),
]
TEMPLATE=["min_age","max_age_application","max_age_at_maturity","min_income","min_cibil","employment_scope","min_current_job_months","min_total_experience_months",
 "min_business_vintage_months","city_restrictions","emi_nmi_max_ratio","foir_max","income_multiple_max","amount_min","amount_max","rate_min","rate_max","tenure_min","tenure_max","processing_fee","salary_account_required"]
out=[]; n=0
for l in L:
    lid=l[0]; have={r[1] for r in R if r[0]==lid}
    for r in R:
        if r[0]==lid:
            n+=1; out.append(dict(rule_id=f"R{n:04d}",lender_id=lid,rule_key=r[1],applicant_category=r[2],value=r[3],unit=r[4],status=r[5],source_ids=r[6],extracted_text=r[7],notes=r[8],date_accessed=ACC))
    for k in TEMPLATE:
        if k not in have:
            n+=1; note="Not found in retrieved snippets; official page not fully read." if l[6] else "Lender not researched in this session (no search performed)."
            out.append(dict(rule_id=f"R{n:04d}",lender_id=lid,rule_key=k,applicant_category="ALL",value="",unit="",status="UNKNOWN",source_ids="",extracted_text="",notes=note,date_accessed=ACC))
w("lender_rules_detailed.csv",out,list(out[0].keys()))
def pick(lid,key):
    rs=[r for r in out if r["lender_id"]==lid and r["rule_key"]==key]
    return ("|".join((r["applicant_category"]+"="+r["value"]) if len(rs)>1 else r["value"] for r in rs),"|".join(sorted({r["status"] for r in rs})))
keys=["min_age","max_age_application","max_age_at_maturity","min_income","min_cibil","emi_nmi_max_ratio","amount_max","rate_min","rate_max","tenure_min","tenure_max","salary_account_required"]
summ=[]
for l in L:
    row=dict(lender_id=l[0],brand_name=l[2])
    for k in keys: row[k],row[k+"_status"]=pick(l[0],k)
    lr=[r for r in out if r["lender_id"]==l[0]]
    row.update(n_rules=len(lr),n_unknown=sum(r["status"]=="UNKNOWN" for r in lr),n_conflicting=sum(r["status"]=="CONFLICTING" for r in lr)); summ.append(row)
w("lender_rule_summary.csv",summ,list(summ[0].keys()))
C=["name","label","type","unit","description","required","allowed_values","source_category","validation","used_by","provided_by"]
V=[
("age","Age","float","years","Completed age at application","Y","18-100","APPLICANT","document-verifiable (DOB)","L01,L02,L13 min/max age & maturity","APPLICANT"),
("employment_type","Employment type","enum","","salaried | self_employed","Y","salaried,self_employed","APPLICANT","document","all (product scope)","APPLICANT"),
("net_monthly_income","Net monthly income","float","INR/month","Take-home salary. Self-employed: documented monthly income only; NOT interchangeable with turnover or profit","Y",">=0","DOCUMENT","salary slips / bank statement","L01,L02 min income; EMI ratio","DOCUMENT"),
("cibil_score","Credit score (CIBIL)","int","points","Bureau score; null if unavailable","Y","300-900 or null","BUREAU","bureau pull with consent","L01,L02,L13","BUREAU"),
("existing_monthly_emi","Existing monthly EMIs","float","INR/month","Sum of EMIs on active loans/cards","Y",">=0","BUREAU","bureau + declaration","L01 EMI/NMI cap; global affordability assumption","BUREAU"),
("salary_account_bank","Salary account bank","enum","","HDFC Bank | SBI | OTHER","N","","DOCUMENT","bank statement","L01 (required), L02 (income tier)","DOCUMENT"),
("requested_amount","Requested loan amount","float","INR","Amount sought","Y",">0","APPLICANT","","compared with estimated max","APPLICANT"),
("preferred_tenure_months","Preferred tenure","int","months","Desired repayment period","Y","3-120","APPLICANT","","tenure limits, EMI","APPLICANT"),
("city","City of residence","string","","Only used if a city rule exists","N","","APPLICANT","address proof","L13 calculator mentions city; no rule found","APPLICANT"),
("current_job_months","Months with current employer","int","months","No verified rule uses it yet; kept to test UNKNOWN handling","N",">=0","DOCUMENT","","none verified","DOCUMENT"),
("total_experience_months","Total work experience","int","months","No verified rule uses it yet","N",">=0","DOCUMENT","","none verified","DOCUMENT"),
("business_vintage_months","Business vintage","int","months","Self-employed only; no verified rule yet","N",">=0","DOCUMENT","ITR/GST","none verified","DOCUMENT"),
("employer_category","Employer category","string","","No verified rule uses it yet","N","","APPLICANT","","none verified","APPLICANT"),
("derived_obligation_ratio","(Derived) obligations ratio","float","ratio","(existing EMI + new EMI)/net income","calculated","0-10","MODEL","","L01 cap; global assumption","CALCULATED"),
]
w("input_variables.csv",[dict(zip(C,v)) for v in V],C)
json.dump({"status_definitions":{
"VERIFIED_OFFICIAL":"Seen on the lender's own page in this session (snippet or fetch).","VERIFIED_SECONDARY":"Seen only on a comparison/third-party page; used as hard rule but flagged.",
"OBSERVED_IN_CALCULATOR":"Calculator description evidence; no numeric value.","ESTIMATED":"Modelling estimate.","UNKNOWN":"Not found/not researched; never zero/false/eligible.",
"CONFLICTING":"Sources disagree, unresolved; engine will not use the value.","NOT_APPLICABLE":"Not relevant."},
"global_affordability_assumption":{"status":"ESTIMATED","emi_to_income_cap":0.5,"method":"S02 (secondary) says most banks/NBFCs cap total EMIs at 50-60% of net income; 0.50 chosen conservatively.","use":"Estimate max loan only for lenders with no published ratio. Never a rejection threshold; raises a warning only.","confidence":"LOW"},
"amount_calculation":"max_amount = min(published amount_max if known, PV(headroom EMI, rate_max, permitted tenure)); headroom = cap*income - existing EMI. rate_max used (conservative) since applicant rate unknown; if rate unknown, only published cap shown."},
open(f"{D}/model_assumptions.json","w"),indent=2)
print("built",len(out),"rule rows")
