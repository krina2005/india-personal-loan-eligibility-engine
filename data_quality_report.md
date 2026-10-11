# Data-quality report (generated)

| Check | Result | Detail |
|---|---|---|
| Exactly 20 distinct lender IDs | PASS |  |
| Summary has exactly 20 rows mapping to lenders | PASS |  |
| Every rule maps to a lender | PASS |  |
| Every rule has a valid status | PASS |  |
| Every verified/observed/conflicting rule has source | PASS | [] |
| All rule source IDs exist in register | PASS |  |
| Every source has ISO access date | PASS |  |
| UNKNOWN rules carry no value | PASS |  |
| No ESTIMATED rules without method (none present) | PASS | estimate lives in model_assumptions.json |
| Profiles >=10 | PASS | 14 |
| Each profile evaluated against all 20 lenders | PASS |  |
| Every NOT_ELIGIBLE has >=1 rejection reason with rule ids | PASS |  |
| No approval-like status for lenders with UNKNOWN core rules | PASS |  |
| [GAP] Every lender has public evidence it offers personal loans | FAIL | only 3/20 verified |
| [GAP] Every lender has researched rules | FAIL | 3/20 researched |

## Rule-status counts (all 20 lenders)

- UNKNOWN: 390
- VERIFIED_OFFICIAL: 21
- VERIFIED_SECONDARY: 7
- CONFLICTING: 3
- OBSERVED_IN_CALCULATOR: 1

## Coverage by lender

| Lender | researched | non-UNKNOWN rules | UNKNOWN | CONFLICTING |
|---|---|---|---|---|
| L01 SBI | PARTIAL | 13 | 9 | 2 |
| L02 HDFC Bank | PARTIAL | 11 | 11 | 0 |
| L03 ICICI Bank | NONE | 0 | 21 | 0 |
| L04 Axis Bank | NONE | 0 | 21 | 0 |
| L05 Kotak Mahindra Bank | NONE | 0 | 21 | 0 |
| L06 IndusInd Bank | NONE | 0 | 21 | 0 |
| L07 Yes Bank | NONE | 0 | 21 | 0 |
| L08 IDFC FIRST Bank | NONE | 0 | 21 | 0 |
| L09 Federal Bank | NONE | 0 | 21 | 0 |
| L10 Bank of Baroda | NONE | 0 | 21 | 0 |
| L11 PNB | NONE | 0 | 21 | 0 |
| L12 Canara Bank | NONE | 0 | 21 | 0 |
| L13 Bajaj Finserv | PARTIAL | 8 | 13 | 1 |
| L14 Tata Capital | NONE | 0 | 21 | 0 |
| L15 Aditya Birla Capital | NONE | 0 | 21 | 0 |
| L16 SMFG India Credit | NONE | 0 | 21 | 0 |
| L17 Hero FinCorp | NONE | 0 | 21 | 0 |
| L18 Poonawalla Fincorp | NONE | 0 | 21 | 0 |
| L19 IIFL Finance | NONE | 0 | 21 | 0 |
| L20 InCred | NONE | 0 | 21 | 0 |