# AUFI Assist: fixed clinical test protocol

**Status:** DRAFT: needs clinician review before use with patients  
**Version:** 1.0.0  
**Scope:** Only ICMR and MoHFW guidelines (MoHFW includes its directorates and programmes: NCVBDC, NCDC, NVHCP, DHR). No WHO, IAP or other-body documents.

Each condition lists first-line tests with the day-of-illness window in which they are valid. Pair differentiators apply when the top two or three conditions are close. Every line carries source ids (see sources) and a section/page locator.

## Sources

| Id | Document | Issuer | Year | Read |
|---|---|---|---|---|
| S01 | Diagnosis and Treatment of Malaria (NVBDCP) | MoHFW | 2013 | full text |
| S02 | National Guidelines for Clinical Management of Dengue Fever (NCVBDC) | MoHFW | 2023 | full text |
| S03 | National Guidelines for Clinical Management of Chikungunya Fever (NCVBDC) | MoHFW | 2023 | full text |
| S04 | Treatment Guidelines for Antimicrobial Use in Common Syndromes, 2nd ed. | ICMR | 2019 | chapters 1-5 read |
| S05 | National Treatment Guidelines for Antimicrobial Use in Infectious Disease Syndromes, v2.0 (NCDC with ICMR) | MoHFW | 2025 | sections 1-9 read |
| S06 | National Guidelines: Diagnosis, Case Management, Prevention and Control of Leptospirosis (NCDC) | MoHFW | 2015 | full text |
| S07 | DHR-ICMR Guidelines for Diagnosis and Management of Rickettsial Diseases in India | ICMR | 2015 | full text |
| S08 | National Guidelines for Diagnosis and Management of Viral Hepatitis (NVHCP) | MoHFW | 2018 | hepatitis A/E sections read |
| S09 | Guidelines on categorization of seasonal influenza cases for testing, treatment and hospitalization (NCDC) | MoHFW | 2016 | excerpts only |
| S10 | Clinical Management Protocol for Seasonal Influenza (NCDC) | MoHFW | 2019 | excerpts only |
| S11 | Guidelines for management of co-infection of COVID-19 with other seasonal epidemic-prone diseases (DGHS) | MoHFW | 2021 | excerpts only |
| S12 | TB screening guidance note (MoHFW, COVID-19 and TB) | MoHFW | 2021 | excerpts only |
| S13 | Standard Treatment Workflow: Acute Rheumatic Fever (DHR, MoHFW) | ICMR | 2024 | excerpts only |

## Baseline work-up by day of fever (all conditions)

- **day 1 2**: Fever day 1-2: defer investigations and antimicrobials unless the patient has features of sepsis. (S05 §3.1 p.27; S04 protocol p.9)
- **day 3 4**: Fever day 3-4: blood count with differential, liver and renal function, urine examination, blood sugar, malaria smear and RDT, and a dengue antigen test if suspicion is high. (S05 §3.1 p.27)
- **day 5 plus**: Fever beyond 5 days: the day 3-4 tests plus two sets of blood cultures and a chest X-ray; add IgM serology for dengue, chikungunya, scrub typhus and leptospirosis according to clinical suspicion. (S05 §3.1 p.27; S04 protocol p.9)
- **day 7 plus**: Fever beyond 7 days: all of the above plus an abdominal ultrasound. (S05 §3.1 p.27; S04 protocol p.9)

## Malaria

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Blood smear for malaria parasite (thick and thin) | blood | any day of illness | Send for every suspected case; repeat once if the first smear is negative in an endemic area. | S04 §2.1.5 p.7; S01 flow charts pp.3-5 |
| Malaria rapid diagnostic test (bivalent Pf/Pv) | blood | any day of illness | Bivalent RDT is used when a microscopy result will not be back within 24 hours; if malaria is still strongly suspected after a negative RDT, also send a slide. | S01 flow charts pp.3-5 |

**Also useful**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| G6PD status (guides primaquine for P. vivax) | blood |  | Primaquine for P. vivax is guided by G6PD status; it is contraindicated in G6PD deficiency, infants and pregnancy. | S04 §2.2.4.3 p.15; S01 p.6 |

**If severe**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Blood smear for malaria parasite (thick and thin) | blood |  | Severe malaria needs a smear with parasite count reported within an hour, plus haemoglobin, blood glucose and urine examination; refer to a facility that can give parenteral treatment. | S01 p.16 |
| Complete blood count with differential, haematocrit and platelet count | blood |  | Haemoglobin for severe anaemia. | S01 p.16 |
| Random blood sugar | blood |  | Hypoglycaemia is a complication of severe malaria. | S01 pp.14,16 |
| Urine routine and microscopy | urine |  | Required in the severe malaria work-up. | S01 p.16 |


## Dengue

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Dengue NS1 antigen (ELISA) | serum | day 1-5 | NS1 is sent for samples collected on day 1 to 5 of fever; the lab should be told the day of onset and the day of collection. | S02 §6.2 p.32; S02 §6.1.1 p.30 |
| Dengue IgM capture ELISA (MAC-ELISA) | serum | after day 5 | IgM is sent after day 5; it is usually detectable by day 5 but can appear later. | S02 §6.2 p.32; S02 §6.1.2 p.30 |
| Dengue RT-PCR | acute-phase serum | early illness, under 5 days | RT-PCR on acute-phase serum has replaced virus isolation as the standard for detecting virus. | S02 §6.1.4 p.31; S11 laboratory testing table |
| Complete blood count with differential, haematocrit and platelet count | blood | any day of illness | Recommended for all patients with warning signs and all patients with fever beyond 3 days; look for leucopenia, falling platelets and a rising haematocrit. | S02 §7.1 p.33; S02 §4.2 p.20 |

**Also useful**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Random blood sugar | blood |  | Recommended together with the blood count in the same patients. | S02 §7.1 p.33 |
| Liver function tests (AST, ALT, bilirubin) | blood |  | Adults, patients with comorbidities, shock or complications. | S02 §7.3 p.35 |
| Renal function tests (urea, creatinine) | blood |  | Adults, patients with comorbidities, shock or complications. | S02 §7.3 p.35 |

**If severe**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Serial haematocrit and platelet count | blood |  | Haematocrit every 4-6 hours in stable cases, more often if unstable; a rise of 10% above baseline is an early sign of plasma leakage. | S02 §7.3 pp.34-35 |
| Chest X-ray (PA view) | - |  | Chest X-ray or ultrasound helps detect plasma leakage. | S02 p.15 |
| Ultrasonography of the abdomen | - |  | Ultrasound helps detect plasma leakage and gall bladder wall thickening. | S02 p.15; S04 §2.3.6.6 p.23 |

**Not recommended**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Dengue rapid antigen/antibody tests | serum |  | The national programme does not recommend rapid tests for diagnosing dengue or guiding management, because accuracy varies from batch to batch. | S02 §6.1.7 pp.31-32 |

> IgG ELISA indicates past infection only and is not a diagnostic test for acute dengue. (S02 §6.1.5 p.31)

## Chikungunya

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Chikungunya RT-PCR | serum or whole blood | day 0-7 | RT-PCR is used between day 0 and day 7 of symptoms (viral RNA is detectable up to about 8 days). | S03 §3.2 p.8; S03 §3.1.3 p.8 |
| Chikungunya IgM capture ELISA (MAC-ELISA) | serum | after day 7 | IgM serology is used after day 7; repeat testing in 5 to 10 days if suspicion persists and the first result is negative. | S03 §3.2 p.8; S03 §3.1.2 p.7 |
| Complete blood count with differential, haematocrit and platelet count | blood | any day of illness | Leucopenia with lymphocyte predominance is usual and severe thrombocytopenia is rare; useful to separate it from dengue. | S03 §3.2 p.8; S03 Table 3 p.12 |

**Also useful**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| ESR and C-reactive protein | blood |  | ESR is usually raised and CRP rises in the acute phase. | S03 §3.2 p.8 |
| Blood smear for malaria parasite (thick and thin) | blood |  | Dengue, malaria and other tropical fevers must be excluded at first contact. | S03 §6.1.2.1 p.26; S03 §4.2 p.11 |

> Dengue and chikungunya can occur together, so a positive result for one does not exclude the other. (S03 §5.3.5 p.20)

## Typhoid

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Blood cultures, two sets, before any antibiotic | blood | any day of illness | Blood culture is the gold standard; two sets are drawn before empiric antibiotics. | S05 §3.2 p.29; S04 §2.1.5 p.7 |
| Complete blood count with differential, haematocrit and platelet count | blood | any day of illness | Part of the day 3-4 baseline work-up for undifferentiated fever. | S05 §3.1 p.27 |

**Not recommended**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Widal test | serum |  | Avoid the Widal test for diagnosis; it may also be negative before the second week of fever. | S05 §3.2 p.29; S02 §8.1.4 p.50 |

> Suspect typhoid with continuous fever, gastrointestinal symptoms and splenomegaly. (S04 §2.1.4 p.6)

## Scrub Typhus

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Skin examination for eschar (neck, axillae, chest, abdomen, groin) and lymph nodes | bedside | any day of illness | An eschar is the single most useful clue; look in moist skin folds, where it may lack the black scab. Also look for regional lymphadenopathy and rash. | S04 §2.1.3 p.6; S07 §2 p.12 |
| Scrub typhus / rickettsial IgM ELISA | serum | from about day 5-7 | IgM capture ELISA is the mainstay of laboratory diagnosis; a significant IgM titre appears at the end of the first week (OD cut-off 0.5). | S07 §3.2.1 p.15; S04 §2.4.4 p.27 |
| Weil-Felix test (OX2, OX19, OXK) | serum | after 5-7 days | Can be used at primary level only after 5 to 7 days of fever; a titre of 1:80 or more suggests possible infection. Low sensitivity. | S07 §3.2.1 p.15 |

**Also useful**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Rickettsial PCR | eschar sample or whole blood | first week | Best on eschar or blood in the first week; available only at a few centres. | S07 §3.2.1 p.15 |
| Complete blood count with differential, haematocrit and platelet count | blood |  | Thrombocytopenia is seen in most patients. | S07 §3.2.2 p.15 |
| Liver function tests (AST, ALT, bilirubin) | blood |  | Raised transaminases are common, with ALT usually higher than AST. | S07 §3.2.2 p.16; S04 §2.4.3 p.26 |
| Chest X-ray (PA view) | - |  | Bilateral infiltrates are common; pneumonia is a frequent complication. | S07 §3.3.3 p.16 |

**Not recommended**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Rapid tests for scrub typhus | serum |  | Rapid tests are not recommended for scrub typhus at the present stage. | S07 §3.2.1 p.15 |

> Suspect a rickettsial infection in an undifferentiated fever of 5 days or more; if an eschar is present, a shorter fever can be scrub typhus. (S07 §3.1.1 p.14)

## Leptospirosis

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Leptospirosis rapid screening test (immunochromatography or slide agglutination) | serum | any day of illness | A rapid test is used for screening at PHC and CHC level; results need confirmation by ELISA. | S06 §4.3 p.14; S06 §5.1 p.17 |
| Leptospirosis IgM ELISA | serum | from about day 5-7 | ELISA can detect antibody earlier than MAT and tells recent from past infection; antibody tests are generally positive only after 5-7 days. | S06 Annexure 1 p.27; S04 §2.1.5 p.7 |
| Serum creatine phosphokinase (CPK) | blood | any day of illness | Marked CPK elevation points to leptospirosis and helps separate it from viral and alcoholic hepatitis. | S06 §3.1.1 p.8; S06 §3.2 pp.10-11 |
| Urine routine and microscopy | urine | any day of illness | Some renal involvement is almost always present: proteinuria, casts, haematuria. | S06 §3.1.1 p.8; S06 §4.3 p.14 |

**Also useful**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Microscopic agglutination test (MAT) for Leptospira | paired sera |  | Gold standard for serovar-specific antibodies; a rising titre between acute and convalescent sera is confirmatory. State or reference laboratory. | S06 §4.1 p.13; S06 Annexure 1 p.26 |
| Leptospira PCR | blood, urine or CSF |  | Useful in the first days when antibodies are not yet detectable; state or reference laboratory. | S06 Annexure 1 p.27 |
| Leptospira culture (EMJH medium) | blood |  | Blood culture within 10 days of onset and before antibiotics; slow and specialised. | S06 Annexure 1 p.23 |
| Liver function tests (AST, ALT, bilirubin) | blood |  | Transaminases are normal or only mildly raised (hundreds of IU/L). | S06 §3.2 p.10 |
| Renal function tests (urea, creatinine) | blood |  | Urea and creatinine are raised when the kidney is involved. | S06 §4.3 p.14 |
| Complete blood count with differential, haematocrit and platelet count | blood |  | Neutrophilia and thrombocytopenia are typical. | S06 §4.3 p.14 |

**Not recommended**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Dark-field microscopy for Leptospira (as a sole test) | blood or urine |  | Dark-field microscopy has low sensitivity and specificity and is not recommended as the only test. | S06 Annexure 1 p.25 |

> Leptospira serology cross-reacts with hepatitis A and E, so read serology together with the enzyme pattern and confirm with MAT or PCR where possible. (S06 Annexure 1 note p.28)

## Viral Ili

**Only if**

- If Category C features: breathlessness, chest pain, drowsiness, low blood pressure, bluish discolouration, or worsening of a chronic illness: Influenza RT-PCR. These patients should be tested for influenza (swab RT-PCR) and hospitalised; empirical oseltamivir is started while the result is pending. (S09 Category C; S10 §3 Investigations; S11 laboratory testing table)

> No influenza test is required for Category A (mild fever with cough or sore throat) or Category B (high-grade fever, severe sore throat, or a high-risk group). (S09 Category A and B)

## Hepatitis A E

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Liver function tests (AST, ALT, bilirubin) | blood | any day of illness | In acute hepatitis with jaundice, bilirubin is above 2.5 mg/dL and ALT is more than 10 times the upper limit of normal. | S08 p.17; S08 p.44 |
| IgM anti-HAV | serum | any day of illness | IgM anti-HAV marks acute hepatitis A; it appears 5-10 days before symptoms and persists up to 6 months. | S08 Laboratory Diagnosis p.17 |
| IgM anti-HEV | serum | any day of illness | Definitive diagnosis of hepatitis E rests on IgM anti-HEV; suspect it when hepatitis A is excluded or when several cases cluster. | S08 Hepatitis E p.44 |

**If severe**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Prothrombin time / INR | blood |  | Suspect acute liver failure with confusion, persistent vomiting, bleeding or hypoglycaemia; refer when sensorium is altered and INR is above 1.5. | S08 pp.45-46 |
| Random blood sugar | blood |  | Repeated hypoglycaemia is a warning sign of liver failure. | S08 p.46 |

> Hepatitis A and E cannot be told apart, or from other viral hepatitis, on clinical grounds alone. (S08 p.44)

## Occult Bacteraemia

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Blood cultures, two sets, before any antibiotic | blood | fever beyond 5 days, or earlier if septic | At least two sets before empiric antibiotics. | S04 §2.1.5 p.7; S05 §3.1 p.27 |
| Urine routine and microscopy | urine | any day of illness | White cells, protein and blood point to a urinary source. | S04 §2.1.5 p.7; S05 §3.1 p.27 |
| Urine culture before antibiotics | midstream urine | any day of illness | Collect before antibiotics when pyelonephritis or urosepsis is possible. | S05 §5.2 p.40 |
| Chest X-ray (PA view) | - | fever beyond 5 days | Chest X-ray looks for an occult pneumonia. | S04 §2.1.5 p.7; S05 §3.1 p.27 |
| Ultrasonography of the abdomen | - | fever beyond 7 days | Ultrasound looks for hepatic, renal or other intra-abdominal sources. | S04 §2.1.5 p.7; S05 §3.1 p.27 |

**Also useful**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Complete blood count with differential, haematocrit and platelet count | blood |  | Leucocytosis can point to a bacterial source. | S04 §2.1.5 p.7 |
| Liver function tests (AST, ALT, bilirubin) | blood |  | Part of the baseline work-up. | S05 §3.1 p.27 |

**If severe**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Serum lactate | blood |  | In suspected sepsis, measure lactate and draw blood cultures before antibiotics. | S04 §3.5 p.30; S05 p.31 |

> The primary source is often occult, most often pneumonia, an intra-abdominal infection or urosepsis, and may be silent in the elderly. (S04 §2.1.4 p.6)

## Rheumatic Fever

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Throat swab rapid streptococcal antigen test | throat swab | any day of illness | Evidence of a preceding streptococcal infection is essential for the diagnosis: throat antigen or culture positive, or a raised ASO titre. | S13 Diagnosis based on Jones criteria |
| Throat swab culture for group A streptococcus | throat swab | any day of illness | Same essential criterion as above. | S13 Diagnosis based on Jones criteria |
| Anti-streptolysin O (ASO) titre | serum | any day of illness | Raised ASO titre (above 320 U) counts as evidence of preceding streptococcal infection. | S13 Diagnosis based on Jones criteria |
| ESR and C-reactive protein | blood | any day of illness | Minor criteria: ESR above 60 mm/h or CRP 3 mg/dL or more with polyarthralgia; ESR above 30 with monoarthralgia. | S13 Diagnosis based on Jones criteria |
| 12-lead ECG | - | any day of illness | A prolonged PR interval for age is a minor criterion unless carditis is already a major criterion. | S13 Diagnosis based on Jones criteria |
| Echocardiogram | - | any day of illness | Monitor for carditis in all patients. | S13 Management |

**Also useful**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Complete blood count with differential, haematocrit and platelet count | blood |  | Total and differential leucocyte count. | S13 Investigations |
| Chest X-ray (PA view) | - |  | Chest X-ray as part of the cardiac assessment. | S13 Investigations |
| Anti-DNase B | serum |  | Optional additional marker of recent streptococcal infection. | S13 Investigations |

> Think of rheumatic fever when there is migratory arthritis after a significant sore throat. (S04 §2.1.4 p.7)

## Tb

**First-line tests**

| Test | Specimen | When valid | Why | Source |
|---|---|---|---|---|
| Chest X-ray (PA view) | - | any day of illness | Chest X-ray in anyone screened positive: cough, fever or significant weight loss/night sweats; also if chest findings are present. | S12 TB screening; S04 §2.1.5 p.7 |
| TB nucleic acid amplification test (CBNAAT / Truenat) | sputum | any day of illness | Upfront nucleic acid amplification test (CBNAAT/Truenat) on a sputum sample in those screened positive. | S12 TB screening |

> Screen for TB with the four-symptom complex: cough or fever for more than 2 weeks, significant weight loss, night sweats. Consider TB in any prolonged undifferentiated fever, especially with weight loss. (S12 TB screening; S04 §2.1.4 p.7)

## When the leading conditions are close

Rule for pairs without an entry below: For a close pair with no explicit entry, send the diagnostic tests of each condition that the other does not share, routine laboratory tests before reference-laboratory tests, filtered to the day of fever when it is known. If nothing remains, send the first-line tests of both.

### Dengue vs Chikungunya

Send: Complete blood count with differential, haematocrit and platelet count; Dengue NS1 antigen (ELISA); Dengue IgM capture ELISA (MAC-ELISA); Chikungunya RT-PCR; Chikungunya IgM capture ELISA (MAC-ELISA).

Leucopenia, thrombocytopenia and a raised haematocrit are common in dengue and infrequent in chikungunya; bleeding, organ involvement and shock are common in severe dengue and rare in chikungunya; polyarthralgia is frequent in chikungunya and less common in dengue. Both can occur together. (S03 Table 3 p.12; S03 §5.3.5 p.20)

### Leptospirosis vs Hepatitis A E

Send: Liver function tests (AST, ALT, bilirubin); Serum creatine phosphokinase (CPK); IgM anti-HAV; IgM anti-HEV; Leptospirosis IgM ELISA; Urine routine and microscopy.

In leptospirosis AST and ALT are normal or only mildly raised and CPK is high; in viral hepatitis ALT is markedly raised and CPK is normal. Leptospira serology cross-reacts with hepatitis A and E, so do not rely on serology alone. (S06 §3.2 pp.10-11; S06 Annexure 1 note p.28)

### Dengue vs Hepatitis A E

Send: Liver function tests (AST, ALT, bilirubin); IgM anti-HAV; IgM anti-HEV; Dengue NS1 antigen (ELISA); Dengue IgM capture ELISA (MAC-ELISA); Complete blood count with differential, haematocrit and platelet count.

Dengue usually causes a mild to moderate transaminase rise with uncommon jaundice, plus falling platelets and rising haematocrit; acute viral hepatitis shows jaundice with bilirubin above 2.5 mg/dL and ALT above 10 times normal. (S04 §2.3.6.3 p.22; S08 p.17)

### Rheumatic Fever vs Chikungunya

Send: Anti-streptolysin O (ASO) titre; Throat swab rapid streptococcal antigen test; 12-lead ECG; ESR and C-reactive protein; Chikungunya RT-PCR; Chikungunya IgM capture ELISA (MAC-ELISA).

Rheumatic fever gives fleeting, migratory arthritis of the large joints, more often in children, after a recent sore throat, with a raised ASO titre and diagnosis by Jones criteria (ECG PR interval, echocardiogram for carditis). Chikungunya gives symmetrical, mainly small-joint polyarthralgia and is confirmed by RT-PCR or IgM. (S03 §4.2 p.11; S03 §5.2.1 p.14; S13 Diagnosis based on Jones criteria)

### Scrub Typhus vs Dengue

Send: Skin examination for eschar (neck, axillae, chest, abdomen, groin) and lymph nodes; Scrub typhus / rickettsial IgM ELISA; Dengue NS1 antigen (ELISA); Dengue IgM capture ELISA (MAC-ELISA); Complete blood count with differential, haematocrit and platelet count; Liver function tests (AST, ALT, bilirubin).

An eschar, regional lymphadenopathy or rash favours scrub typhus. Both can cause low platelets and mild hepatitis, so serology decides; a rising haematocrit favours dengue. (S04 §2.1.4 p.6; S04 conclusion p.27; S02 §7.3 p.34)

### Scrub Typhus vs Leptospirosis

Send: Skin examination for eschar (neck, axillae, chest, abdomen, groin) and lymph nodes; Scrub typhus / rickettsial IgM ELISA; Leptospirosis IgM ELISA; Leptospirosis rapid screening test (immunochromatography or slide agglutination); Serum creatine phosphokinase (CPK); Urine routine and microscopy.

Eschar and lymphadenopathy point to scrub typhus; conjunctival suffusion, calf muscle tenderness, a high CPK and urine abnormalities point to leptospirosis. (S04 §2.1.4 p.6; S06 §3.1.1 p.8; S07 §2 p.12)

### Typhoid vs Occult Bacteraemia

Send: Blood cultures, two sets, before any antibiotic; Urine routine and microscopy; Urine culture before antibiotics; Chest X-ray (PA view); Ultrasonography of the abdomen.

Blood culture serves both. A chest, urinary or abdominal focus on X-ray, urine tests or ultrasound supports secondary bacteraemia; continuous fever with gastrointestinal symptoms and splenomegaly supports typhoid. (S04 §2.1.4 p.6; S04 §2.1.5 p.7)

### Tb vs Occult Bacteraemia

Send: TB nucleic acid amplification test (CBNAAT / Truenat); Chest X-ray (PA view); Blood cultures, two sets, before any antibiotic.

Prolonged fever with weight loss or night sweats calls for chest X-ray and NAAT; bacteraemia needs cultures and a search for a focus. Avoid empiric fluoroquinolones where TB is possible, because they can mask TB. (S12 TB screening; S04 §4.3.3 p.39)

### Viral Ili vs Dengue

Send: Dengue NS1 antigen (ELISA); Dengue IgM capture ELISA (MAC-ELISA); Blood smear for malaria parasite (thick and thin); Malaria rapid diagnostic test (bivalent Pf/Pv).

Mild influenza-like illness needs no influenza test (influenza RT-PCR only for Category C), so the useful tests are those for dengue and malaria, which have specific management. (S09 Category A and B; S02 §6 p.30)

### Malaria vs Dengue

Send: Blood smear for malaria parasite (thick and thin); Malaria rapid diagnostic test (bivalent Pf/Pv); Dengue NS1 antigen (ELISA); Dengue IgM capture ELISA (MAC-ELISA); Complete blood count with differential, haematocrit and platelet count.

Malaria should be excluded in every acute undifferentiated fever, because it has specific treatment and can coexist with dengue. (S04 §2.1.4 p.6; S02 §8.1.4 p.49)

## Where the guidelines disagree

- Dengue rapid tests: ICMR 2019 (S04 §2.1.5) lists a dengue rapid NS1 antigen test; NCVBDC 2023 (S02 §6.1.7) does not recommend rapid tests. This protocol follows NCVBDC, the national programme and the later document.
- Day 3-4 baseline: ICMR 2019 lists blood count, malaria smear and RDT; the joint NCDC-ICMR 2025 guideline adds liver and renal function, urine examination and blood sugar. This protocol follows the 2025 version.
- Dengue NS1 window: NCVBDC 2023 says NS1 for day 1-5 and IgM after day 5; ICMR 2019 says NS1 can diagnose during the first week. This protocol uses NCVBDC.

## Open items before clinical use

- TB: the four-symptom screen, chest X-ray and upfront NAAT come from a MoHFW note (S12) read in excerpt. Confirm against the current NTEP Technical and Operational Guidelines, including whether sputum smear remains first-line in your setting and that antibody (serology) tests are not to be used (relayed by secondary summaries only, so not included).
- Influenza, rheumatic fever, TB and co-infection sources (S09-S13) were read as excerpts; confirm the exact wording against the full documents.
- Page numbers are the printed page numbers seen in the documents and may differ from PDF page numbers.
- No clinician has reviewed this file yet. Marked as DRAFT until one signs it off.
