# Error Examples (10 sampled, seed=42)
Total errors: 172 / 300 questions
Bucket definitions:
- **Parse failure**: model output could not be parsed to a letter
- **Retrieval miss**: no top-5 chunk contained key terms from correct answer
- **Model ignored context**: relevant chunk retrieved but wrong answer given
- **Other**: answer was parseable, relevant chunk retrieved but still wrong; or correct answer had no extractable key terms

---

## Error 1 — Model ignored context

**Question ID**: `medqa_test_327`

**Question**: A 22-year-old man from Nepal presents to the emergency department complaining of swelling and pain in his right testicle. The patient states that he just arrived in the United States to live with his wife, with whom he is monogamous. The patient denies painful urination or urethral discharge, but admits that 10 days ago he “felt like he had a fever” and the right side of his face was swollen and painful. Which of the following is characteristic of the most likely diagnosis?

**Options**: (A) Preventable by a live attenuated vaccine | (B) Dilation of the pampiniform plexus | (C) Original presentation in the form of a painless chancre | (D) Cause buboes in the inguinal lymph nodes | (E) Is a common cause of septic arthritis in this patient’s age group

**Correct**: (A) Preventable by a live attenuated vaccine

**Predicted**: D

**Generated answer (first 300 chars)**:
> Based on the provided medical context, I can try to help you answer the question.

The patient presents with swelling and pain in his right testicle, which is likely due to epididymo-orchitis. The patient also mentions that 10 days ago, he had a fever and the right side of his face was swollen and p…

**Top-2 retrieved snippets**:
1. [Anatomy_Gray.txt] descends into the scrotum and up onto the anterior abdominal wall deep to the superficial fascia. In association with severe pelvic fractures, urethral rupture may occur at the prostatomembranous junction above the deep perineal pouch. The urine will extravasate into the true pelvis. The worst and m…
2. [InternalMed_Harrison.txt] Alternatively, urethritis can be assayed noninvasively by examination of a first-void urine sample for pyuria, either by microscopy or by the leukocyte esterase test. Urine (or a urethral swab) can also be tested directly for chlamydiae by DNA amplification methods, as described below (see “Detectio…

---

## Error 2 — Parse failure

**Question ID**: `medqa_test_514`

**Question**: A 3-year-old girl is brought to the physician because of a 3-day history of fever, cough, purulent nasal discharge. She has experienced 7 similar episodes, each lasting 2–5 days in the previous 2 years. She has also had intermittent abdominal cramps and recurrent episodes of foul-smelling greasy diarrhea in the past year. She is at the 55th percentile for height and 35th percentile for weight. Her temperature is 38.9°C (102°F), pulse is 100/min, respirations are 24/min, and blood pressure is 110/60 mm Hg. Physical examination shows an erythematous oropharynx without exudate and tenderness over the frontoethmoidal sinuses. The abdomen is distended, nontender, and tympanitic to percussion. Bowel sounds are increased. Stool microscopy shows pear-shaped multi-flagellated organisms. This patient is at increased risk for which of the following?

**Options**: (A) Progressive peripheral neuropathy | (B) Anaphylactic transfusion reactions | (C) Cutaneous granulomas | (D) Non-Hodgkin lymphoma | (E) Disseminated tuberculosis

**Correct**: (B) Anaphylactic transfusion reactions

**Predicted**: UNPARSED

**Generated answer (first 300 chars)**:
> Based on the provided medical context, I did not find sufficient information to answer the question accurately. The context does not contain information about the patient's specific condition or diagnosis, making it difficult to determine which option is correct.…

**Top-2 retrieved snippets**:
1. [Pediatrics_Nelson.txt] of the ambulatory patient with a sore throat, Curr Clin Top Infect Dis 9:62–75, 1988. The onset of streptococcal pharyngitis is often rapid and associated with prominent sore throat and moderate to high fever. Headache, nausea, vomiting, and abdominal pain are frequent. In a typical, florid case, th…
2. [InternalMed_Harrison.txt] emergency, particularly in children, and prompt diagnosis and airway protection are of the utmost importance. Etiology After the introduction of the Hib vaccine in the mid-1980s, disease incidence among children in the United States declined dramatically. Nevertheless, lack of vaccination or vaccine…

---

## Error 3 — Parse failure

**Question ID**: `medqa_test_265`

**Question**: A 76-year-old man with chronic obstructive pulmonary disease (COPD) presents complaining of 3 weeks of cough and progressive dyspnea on exertion in the setting of a 20 pound weight loss. He is a 60 pack-year smoker, worked as a shipbuilder 30 years ago, and recently traveled to Ohio to visit family. Chest radiograph shows increased bronchovascular markings, reticular parenchymal opacities, and multiple pleural plaques. Labs are unremarkable except for a slight anemia. Which of the following is the most likely finding on this patient's chest CT?

**Options**: (A) Nodular mass spreading along pleural surfaces | (B) Honeycombing | (C) Air bronchogram | (D) Granulomatous nodule | (E) Lower lobe cavitary mass

**Correct**: (E) Lower lobe cavitary mass

**Predicted**: UNPARSED

**Generated answer (first 300 chars)**:
> Based on the retrieved medical context, I would say that the answer is not present in the given text. The text only describes various medical conditions and their symptoms, radiographic features, and treatment options. It does not specifically discuss the chest CT findings in a patient with COPD, pl…

**Top-2 retrieved snippets**:
1. [InternalMed_Harrison.txt] with a persistent chronic cough and sputum production accompanied by consistent radiographic features. Although chest radiographs lack sensitivity, the presence of “tram tracks” indicating dilated airways is consistent with bronchiectasis. Chest computed tomography (CT) is more specific for bronchie…
2. [InternalMed_Harrison.txt] 300-5 Large bilateral proximal PE on a coronal chest CT image in a 54-year-old man with lung cancer and brain metastases. He had developed sudden onset of chest heaviness and shortness of breath while at home. There are filling defects in the main and segmental pulmonary arteries bilaterally (white …

---

## Error 4 — Retrieval miss

**Question ID**: `medqa_test_1061`

**Question**: A 37-year-old woman presents to the emergency department with confusion, anxiety, sweating, and episodes of vomiting. She is accompanied by her sister who says that her symptoms developed acutely and is unsure about what caused it. She is currently on methimazole, which she last took approximately 1 week ago. Approximately 5 days ago she developed an upper respiratory infection managed with bed rest and ibuprofen. Her temperature is 105°F (40.6°C), blood pressure is 95/68 mmHg, pulse is 145/min, and respirations are 23/min. On physical examination, the patient has altered mentation and is agitated and diaphoretic. The patient also has a goiter, exophthalmos, warm skin, and a hand tremor. She is started on intravenous fluids. Which of the following is the best treatment option for this patient?

**Options**: (A) Antibiotics | (B) Carotid massage | (C) Clonazepam | (D) Epinephrine | (E) Propranolol

**Correct**: (E) Propranolol

**Predicted**: B

**Generated answer (first 300 chars)**:
> Based on the provided medical context, the correct answer is B: Carotid massage.

The patient is experiencing a thyroid storm, which is a life-threatening condition that requires immediate attention. The context suggests that the patient has an underlying thyroid condition (goiter and exophthalmos) …

**Top-2 retrieved snippets**:
1. [Pharmacology_Katzung.txt] four times daily or 5–10 mg/h by intravenous infusion (asthmatic patients only). Release of thyroid hormones from the gland is retarded by the administration of saturated solution of potassium iodide, 5 drops orally every 6 hours starting 1 hour after giving thioamides. Hormone synthesis is blocked …
2. [InternalMed_Harrison.txt] within the incubation period for a given syndrome. Except in infections with Seoul, dengue, and yellow fever viruses, which have urban hosts/vectors, travel to a rural setting is especially suggestive of a diagnosis of VHF. In addition, several diseases considered in the differential diagnosis—falci…

---

## Error 5 — Retrieval miss

**Question ID**: `medqa_test_1193`

**Question**: A 45-year-old man comes to the physician for a routine health maintenance examination. He was diagnosed with HIV 15 years ago. He was taking triple antiretroviral therapy but stopped a few months ago because he was feeling well. He lives in Wyoming. Vital signs are within normal limits. Cardiopulmonary examination shows no abnormalities. His CD4+ T-lymphocyte count is 47/mm3 (N ≥ 500). The patient currently refuses to restart antiretroviral therapy. Which of the following medication regimens is most appropriate at this time?

**Options**: (A) Trimethoprim and sulfamethoxazole | (B) Azithromycin and itraconazole | (C) Azithromycin and amphotericin B | (D) Trimethoprim, sulfamethoxazole, azithromycin | (E) Dapsone, pyrimethamine, itraconazole, azithromycin

**Correct**: (D) Trimethoprim, sulfamethoxazole, azithromycin

**Predicted**: E

**Generated answer (first 300 chars)**:
> Based on the retrieved medical context, the correct answer is:

E: Dapsone, pyrimethamine, itraconazole, azithromycin

This option is the most appropriate at this time because the patient has a CD4+ T-lymphocyte count of 47/mm3, which is below 200/μL. This indicates that the patient is at high risk …

**Top-2 retrieved snippets**:
1. [InternalMed_Harrison.txt] future options for the patient. 7. Women should receive optimal antiretroviral therapy regardless of pregnancy status. 8. The same principles apply to children and adults. The treatment of HIV-infected children involves unique pharmacologic, virologic, and immunologic considerations. 9. Compliance i…
2. [InternalMed_Harrison.txt] regimen with at least two new active drugs. This decision can be guided by resistance testing (see below). In the patient in whom a change is made for reasons of drug toxicity, a simple replacement of one drug is reasonable. It should be stressed that in attempting to sort out a drug toxicity it may…

---

## Error 6 — Parse failure

**Question ID**: `medqa_test_377`

**Question**: A 30-year-old primigravid woman at 22 weeks' gestation is brought to the emergency department by her husband for lethargy, nausea, and vomiting for 4 days. This morning she became drowsy. She returned from a business trip to Sudan 3 weeks ago. She denies eating any seafood while traveling. Medications include iron supplements and a multivitamin. Her immunizations are up-to-date and she has never received blood products. Her temperature is 38.9°C (102°F), pulse is 92/min, and blood pressure is 122/76 mm Hg. She is oriented to person and place. Examination shows jaundice and mild asterixis. Pelvic examination shows a uterus consistent in size with a 22-week gestation. Laboratory studies show:
Hemoglobin 11.2 g/dL
Prothrombin time 18 sec (INR=2.0)
Serum
Total bilirubin 4.4 mg/dL
Alkaline phosphatase 398 U/L
AST 4,702 U/L
ALT 3,551 U/L
Lactate dehydrogenase 3,412 U/L
Anti-nuclear antibody negative
Anti-smooth muscle antibody negative
Anti-CMV antibody negative
Anti-EBV nuclear antigen antibody negative
An ELISA for HIV is negative. Which of the following is most likely to confirm the diagnosis?"

**Options**: (A) HBsAg | (B) Anti-HAV IgG | (C) HCV RNA | (D) Anti-HCV IgG | (E) Anti-HEV IgM

**Correct**: (E) Anti-HEV IgM

**Predicted**: UNPARSED

**Generated answer (first 300 chars)**:
> Based on the provided medical context, the most likely diagnosis is liver disease, possibly related to a viral infection.

The patient's symptoms, including lethargy, nausea, and vomiting, suggest a possible liver-related issue. The laboratory studies show:

* Jaundice and mild asterixis, indicating…

**Top-2 retrieved snippets**:
1. [Obstentrics_Williams.txt] Outcome of pregnancy in sickle cell disease patients attending a combined obstetric and haematology clinic. ) Obstet Gynaecol 29(6):512, 2009 Zhen L, Pen M, Han), et al: Non-invasive prenatal detection of haemoglobin Bart's disease by cardiothoracic ratio during the irst trimester. Eurt) Obstet Gyne…
2. [Obstentrics_Williams.txt] Piel FB, Weatherall 0]: he .-halassemias. N Engl J Med 371:20, 2014 Pinto FO, Roberts I: Cord blood stem cell transplantation for haemoglobinopathies. Br J Haematol 141t(3):309,t2008 Platt OS: Hydroxyurea for the treatment of sickle cell anemia. N Engl ] Med 358: 1362, 2008 Prabu P, Parapia LA: Bern…

---

## Error 7 — Parse failure

**Question ID**: `medqa_test_333`

**Question**: A 36-year-old man is brought to the emergency department 25 minutes after being involved in a high speed motor-vehicle collision in which he was an unrestrained passenger. He has acute myeloid leukemia and is currently receiving chemotherapy. On arrival, his temperature is 37°C (98.6°F), pulse is 63/min, respirations are 10/min, and blood pressure is 100/70 mm Hg. The pupils are equal and sluggish. There are multiple bruises over the face, trunk, and right upper and lower extremities. There is a 4-cm (1.6-in) laceration over his right cheek. He does not respond to any commands, but does groan. Painful stimuli cause him to open his eyes and withdraw all extremities. There are decreased breath sounds over the right lung base. There is tenderness to palpation over the left chest wall. Cardiac examination shows no abnormalities. The abdomen is soft and shows diffuse tenderness to palpation with no guarding or rebound. There is swelling of the right elbow and wrist. The right lower extremity is shorter than the left lower extremity. There are 2 lacerations around 2 cm (0.8 in) each on the right leg. The right knee is swollen. Which of the following is the most appropriate next step in management?

**Options**: (A) Focussed assessment sonography for trauma (FAST) | (B) Insertion of intercostal chest tube | (C) CT scan of the head and neck | (D) X-rays of the extremities | (E) Intubation and mechanical ventilation

**Correct**: (E) Intubation and mechanical ventilation

**Predicted**: UNPARSED

**Generated answer (first 300 chars)**:
> I apologize, but the provided context does not contain information about the patient's symptoms, physical findings, or laboratory results that would indicate a diagnosis of acute myeloid leukemia (AML). Therefore, I cannot provide an answer to this question based on the given context.

However, I ca…

**Top-2 retrieved snippets**:
1. [InternalMed_Harrison.txt] months before the leukemia was diagnosed. Half of patients mention fatigue as the first symptom, but most complain of fatigue or weakness at the time of diagnosis. Anorexia and weight loss are common. Fever with or without an identifiable infection is the initial symptom in approximately 10% of pati…
2. [InternalMed_Harrison.txt] with red cell mass elevation and indirectly to the increased turnover of red cells, leukocytes, and platelets with the attendant increase in uric acid and cytokine production. The latter appears to be responsible for constitutional symptoms. Peptic ulcer disease can also be due to Helicobacter pylor…

---

## Error 8 — Parse failure

**Question ID**: `medqa_test_244`

**Question**: An unidentified surgical specimen is received for histopathologic analysis. A portion of the specimen is cut and stained with hematoxylin and eosin. The remainder is analyzed and is found to contains type II collagen and chondroitin sulfate. Which of the following structures is most likely the origin of this surgical specimen?

**Options**: (A) Blood vessel | (B) Pinna | (C) Pubic symphysis | (D) Lens | (E) Larynx

**Correct**: (E) Larynx

**Predicted**: UNPARSED

**Generated answer (first 300 chars)**:
> I'll do my best to answer your question based on the provided medical context.

After reviewing the context, I noticed that there is no specific mention of the surgical specimen's location or type. However, I did find some information that might be relevant to your question.

One of the passages men…

**Top-2 retrieved snippets**:
1. [Histology_Ross.txt] of type IX collagen is also present in the capsular matrix.  The territorial matrix is a region that is more removed from the immediate vicinity of the chondrocytes. It surrounds the isogenous group and contains a randomly arranged network of type II collagen fibrils with smaller quantities of type…
2. [Histology_Ross.txt] a homogeneous appearance as a result of the orderly packing of the individual collagen fibrils. The nuclei of the tendinocytes appear as elongate profiles arranged in linear rows. The cytoplasm of these cells blends in with the collagen, leaving only the nuclei as the representative feature of the c…

---

## Error 9 — Model ignored context

**Question ID**: `medqa_test_1239`

**Question**: A 7-year-old boy is brought to the clinic by his mother with increasing swelling of his right jaw for the past 2 months. She notes that he has been treated several times with different antibiotics, but that they have not helped. She reports no recent history of fever, chills, or night sweats. The boy has no significant medical history. He emigrated to the United States with his family from Nigeria 1 month ago. He is in the 85th percentile for height and weight, and he has been meeting all developmental milestones. His temperature is 37.8℃ (100.0℉). On physical examination, the patient has a prominent 8 × 8 cm mass over the right mandible. The mass has partially distorted the borders of the mandible and cheek. The overlying skin is erythematous. The mass is firm, immobile, and tender. The contralateral side of the face shows no abnormalities. An oral examination shows the disruption of the ipsilateral lower teeth and oral mucosa. The remainder of the physical exam is unremarkable. A biopsy of the mass is performed and a histopathologic analysis is seen in the image. Which of the following microorganisms is most likely associated with this patient’s condition?

**Options**: (A) Babesia microti | (B) Bartonella henselae | (C) Cytomegalovirus (CMV) | (D) Epstein barr virus (EBV) | (E) Yersinia pestis

**Correct**: (D) Epstein barr virus (EBV)

**Predicted**: B

**Generated answer (first 300 chars)**:
> I'm a medical expert assistant, and I'll do my best to provide an accurate answer.

After reviewing the context, I didn't find any specific information that directly relates to the patient's condition or the biopsy results. However, I can try to narrow down the options based on the patient's symptom…

**Top-2 retrieved snippets**:
1. [Pediatrics_Nelson.txt] necrophorum. Ludwig angina is a mixed anaerobic bacterial cellulitis of the submandibular and sublingual regions. Although often applied to any infection of the sublingual or submandibular region, the term originally was reserved for a rapidly spreading bilateral cellulitis of the sublingual and sub…
2. [First_Aid_Step2.txt] What are the appropriate steps in management? The most common 1° immunodeficiency. An infant has a high fever and onset of rash as fever breaks. What is he at risk for? What is the immunodeficiency? A boy has chronic respiratory infections. Nitroblue tetrazolium test is . A child has eczema, thrombo…

---

## Error 10 — Parse failure

**Question ID**: `medqa_test_1211`

**Question**: A 40-year-old woman comes to the physician because of a 2-month history of increasingly frequent episodes of vertigo and feeling unsteady while walking. She reports that she has had episodic tinnitus in her right ear for the past 3 years. Neurologic examination shows hearing loss in the right ear. An MRI of the brain is shown. Pathologic examination of this patient's lesion is most likely to show which of the following?

**Options**: (A) Whorls of densely packed cells with areas of lamellated calcification | (B) Small blue cells arranged in rosettes around a central neuropil | (C) Hypercellular areas of spindle cells and hypocellular areas of myxoid stroma | (D) Pleomorphic cells clustered around necrotic areas forming pseudopalisades | (E) Cells with clear cytoplasm and central round nucleus resembling a fried egg

**Correct**: (C) Hypercellular areas of spindle cells and hypocellular areas of myxoid stroma

**Predicted**: UNPARSED

**Generated answer (first 300 chars)**:
> Based on the provided medical context, I can say that the answer is not explicitly stated in the context. However, I can try to analyze the symptoms and MRI findings to make an educated guess.

The patient has a history of vertigo and tinnitus, and the MRI shows a lesion. Given the symptoms and the …

**Top-2 retrieved snippets**:
1. [Neurology_Adams.txt] is hearing loss, cerebellar ataxia, and sometimes “screaming tinnitus” or lesser degrees of tonal tinnitus. Also reported is a clinical syndrome of unknown nature consisting of a single abrupt attack of severe vertigo, nausea, and vomiting without tinnitus or hearing loss but with permanent ablation…
2. [InternalMed_Harrison.txt] (conductive vs sensorineural vs mixed), (2) the severity of the impairment (mild, moderate, severe, or profound), (3) the anatomy of the impairment (external ear, middle ear, inner ear, or central auditory pathway), and (4) the etiology. The history should elicit characteristics of the hearing loss,…

---
