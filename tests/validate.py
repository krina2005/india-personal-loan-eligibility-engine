"""Data-quality checks (Part 11). Run: python tests/validate.py  -> prints and writes data_quality_report.md"""
import csv, json, os, collections, re
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
rd=lambda n:list(csv.DictReader(open(f"{B}/data/{n}",encoding="utf-8")))
L,R,S,Sum,V=rd("lenders.csv"),rd("lender_rules_detailed.csv"),rd("sources.csv"),rd("lender_rule_summary.csv"),rd("input_variables.csv")
res=json.load(open(f"{B}/tests/results.json")); json.load(open(f"{B}/data/model_assumptions.json"))
sid={s["source_id"] for s in S}; STAT={"VERIFIED_OFFICIAL","VERIFIED_SECONDARY","OBSERVED_IN_CALCULATOR","ESTIMATED","UNKNOWN","CONFLICTING","NOT_APPLICABLE"}
chk=[]
def c(name,ok,detail=""): chk.append((name,bool(ok),detail))
c("Exactly 20 distinct lender IDs",len({l["lender_id"] for l in L})==20 and len(L)==20)
c("Summary has exactly 20 rows mapping to lenders",len(Sum)==20 and {r["lender_id"] for r in Sum}=={l["lender_id"] for l in L})
c("Every rule maps to a lender",all(r["lender_id"] in {l["lender_id"] for l in L} for r in R))
c("Every rule has a valid status",all(r["status"] in STAT for r in R))
bad=[r["rule_id"] for r in R if r["status"] in {"VERIFIED_OFFICIAL","VERIFIED_SECONDARY","OBSERVED_IN_CALCULATOR","CONFLICTING"} and not r["source_ids"]]
c("Every verified/observed/conflicting rule has source",not bad,str(bad))
c("All rule source IDs exist in register",all(x in sid for r in R for x in r["source_ids"].split(";") if x))
c("Every source has ISO access date",all(re.fullmatch(r"\d{4}-\d{2}-\d{2}",s["date_accessed"]) for s in S))
c("UNKNOWN rules carry no value",all(r["value"]=="" for r in R if r["status"]=="UNKNOWN"))
c("No ESTIMATED rules without method (none present)",all(r["status"]!="ESTIMATED" for r in R),"estimate lives in model_assumptions.json")
c("Profiles >=10",len(res)>=10,str(len(res)))
c("Each profile evaluated against all 20 lenders",all(len(p["lenders"])==20 for p in res))
c("Every NOT_ELIGIBLE has >=1 rejection reason with rule ids",all(l["rejection_reasons"] and all(x["rule_ids"] for x in l["rejection_reasons"]) for p in res for l in p["lenders"] if l["status"]=="NOT_ELIGIBLE"))
c("No approval-like status for lenders with UNKNOWN core rules",all(l["status"]!="POTENTIALLY_ELIGIBLE" for p in res for l in p["lenders"] if l["lender_id"] not in("L01","L02")))
ver=sum(l["offers_pl_evidence_status"]=="VERIFIED_OFFICIAL_PAGE" for l in L)
c("[GAP] Every lender has public evidence it offers personal loans",ver==20,f"only {ver}/20 verified")
c("[GAP] Every lender has researched rules",sum(l["rules_research_depth"]!="NONE" for l in L)==20,f"{sum(l['rules_research_depth']!='NONE' for l in L)}/20 researched")
st=collections.Counter(r["status"] for r in R)
md=["# Data-quality report (generated)\n","| Check | Result | Detail |","|---|---|---|"]+[f"| {n} | {'PASS' if o else 'FAIL'} | {d} |" for n,o,d in chk]
md+=["\n## Rule-status counts (all 20 lenders)\n"]+[f"- {k}: {v}" for k,v in st.most_common()]
md+=["\n## Coverage by lender\n","| Lender | researched | non-UNKNOWN rules | UNKNOWN | CONFLICTING |","|---|---|---|---|---|"]
for l in L:
    rs=[r for r in R if r["lender_id"]==l["lender_id"]]
    md.append(f"| {l['lender_id']} {l['brand_name']} | {l['rules_research_depth']} | {sum(r['status']!='UNKNOWN' for r in rs)} | {sum(r['status']=='UNKNOWN' for r in rs)} | {sum(r['status']=='CONFLICTING' for r in rs)} |")
open(f"{B}/data_quality_report.md","w").write("\n".join(md)); print("\n".join(md[:22]))
