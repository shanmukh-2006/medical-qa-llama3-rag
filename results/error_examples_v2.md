# Error Examples — RAG v2 (10 sampled, seed=42)
Total errors: 144 / 300 questions

Bucket definitions:
- **Parse failure**: model output could not be parsed to a letter
- **Retrieval miss**: no top-5 chunk contained key terms from correct answer
- **Model ignored context**: relevant chunk retrieved but wrong answer given
- **Other**: correct answer had no extractable key terms; answer parseable

---

## Error 1 — Retrieval miss

**Question ID**: `medqa_test_170`

**Question**: A 25-year-old man presents to the emergency department with altered mental status. He was found down in the middle of the street. His past medical history is unknown. His temperature is 99.0°F (37.2°C), blood pressure is 104/64 mmHg, pulse is 70/min, respirations are 5/min, and oxygen saturation is 91% on room air. The patient is being resuscitated in the trauma bay. Which of the following was most likely to be found on exam?

**Options**: (A) Ataxia | (B) Conjunctival injection | (C) Miosis | (D) Mydriasis | (E) Nystagmus

**Correct**: (C) Miosis

**Predicted**: D

**Generated answer (first 300 chars)**:
> Answer: D…

**Top-2 retrieved snippets**:
1. [First_Aid_Step2.txt] eye response, five points for verbal response, and six points for motor response. Patients with chest trauma and shock may have cardiac tamponade. The relevant signs are JVD, hypotension, and mufﬂed heart sounds. This can be diagnosed with bedside ultrasound. If tamponade is diagnosed, an immediate …
2. [Pediatrics_Nelson.txt] are indicators for fluid resuscitation, initiation of chest compressions, or both. When assessment of the ABCs is complete and measures have been taken to achieve an acceptable level of tissue oxygenation, a more complete physical examination is performed. The sequence of this examination depends on…

---

## Error 2 — Retrieval miss

**Question ID**: `medqa_test_1234`

**Question**: A 25-year-old woman comes to the physician because of an acute, painful swelling of the left labia that she first noticed that morning. She also reports some pain while sitting and walking. She is sexually active with her boyfriend and states that she has been having pain during vaginal intercourse lately. She has no history of serious illness. She appears uncomfortable. Her temperature is 38°C (100.4°F), pulse is 90/min, and blood pressure 120/80 mm Hg. Pelvic examination shows a left-sided, tender mass surrounded by edema and erythema in the left inner labia. The remainder of the examination shows no abnormalities. Which of the following is the most appropriate next step in management?

**Options**: (A) Sitz baths | (B) Cryotherapy | (C) Incision and drainage | (D) Biopsy | (E) Trimethoprim-sulfamethoxazole

**Correct**: (C) Incision and drainage

**Predicted**: A

**Generated answer (first 300 chars)**:
> Answer: A…

**Top-2 retrieved snippets**:
1. [Gynecology_Novak.txt] should perform the surgery in a hospital with the necessary support and consultative services to optimize the patient’s outcome (266). When a malignant ovarian mass is discovered and the appropriate surgical staging and debulking procedure cannot be performed by the generalist obstetrician-gynecolog…
2. [Gynecology_Novak.txt] the vulva occur on the labia majora and minora (60%), but the clitoris (15%) and perineum (10%) may be primary sites. Approximately 10% of the cases are too extensive to determine a site of origin, and about 5% of the cases are multifocal. As part of the clinical evaluation, a careful assessment of …

---

## Error 3 — Model ignored context

**Question ID**: `medqa_test_220`

**Question**: A 48-year-old man seeks evaluation at a clinic with a complaint of breathlessness for the past couple of weeks. He says that he finds it difficult to walk a few blocks and has to rest. He also complains of a cough for the past 3 months, which is dry and hacking in nature. The medical history is relevant for an idiopathic arrhythmia for which he takes amiodarone daily. He is a non-smoker and does not drink alcohol. He denies any use of illicit drugs. The vital signs are as follows: heart rate 98/min, respiratory rate 16/min, temperature 37.6°C (99.68°F), and blood pressure 132/70 mm Hg. The physical examination is significant for inspiratory crackles over the lung bases. An echocardiogram shows a normal ejection fraction. A chest radiograph is performed and shown below. Which of the following findings will most likely be noted on spirometry?

**Options**: (A) Decreased FEV1 and normal FVC | (B) Decreased FEV1 and FVC with decreased FEV1/FVC ratio | (C) Normal FEV1 and FVC | (D) Decreased FEV1 and FVC with normal FEV1/FVC ratio | (E) Increased FEV1 and FVC

**Correct**: (D) Decreased FEV1 and FVC with normal FEV1/FVC ratio

**Predicted**: A

**Generated answer (first 300 chars)**:
> Answer: A…

**Top-2 retrieved snippets**:
1. [InternalMed_Harrison.txt] engage and how these activities have changed over time. Dyspnea on exertion is often an early symptom of underlying lung or heart disease and warrants a thorough evaluation. Cough generally indicates disease of the respiratory system. The clinician should inquire about the duration of the cough, whe…
2. [InternalMed_Harrison.txt] of the lung do not manifest as gas exchange abnormalities. As with the evaluation of most patients, the approach to a patient with disease of the respiratory system begins with a thorough history and a focused physical examination. Many patients will subsequently undergo pulmonary function testing, …

---

## Error 4 — Model ignored context

**Question ID**: `medqa_test_519`

**Question**: A 36-year-old man is brought to the emergency department 40 minutes after being involved in a shooting. He sustained a gunshot wound in an altercation outside of a bar. On arrival, he is oriented to person but not to place or time. His temperature is 37.3°C (99.1°F), pulse is 116/min, respirations are 18/min, and blood pressure is 79/42 mm Hg. Pulse oximetry on room air shows an oxygen saturation of 97%. Examination shows multiple abrasions over the arms and thorax. There is a 1-cm (0.4-in) entry wound with minimal bleeding on the right side of the chest in the 6th intercostal space at the midclavicular line. Cardiopulmonary examination shows no abnormalities. Abdominal examination shows diffuse mild tenderness to palpation with no guarding or rebound. A focused assessment with sonography shows no obvious free fluid in the pericardium; assessment of the abdomen is equivocal. An x-ray of the chest shows mild opacification of the right lower lobe. Two large-bore cannulas are inserted and intravenous fluid resuscitation is begun. The patient is intubated and mechanical ventilation is begun. Which of the following is the most appropriate next step in management?

**Options**: (A) Chest tube insertion in the fifth intercostal space at the midaxillary line | (B) CT scan of the chest, abdomen, and pelvis | (C) Local wound exploration | (D) Exploratory laparotomy | (E) Video-assisted thoracoscopic surgery

**Correct**: (D) Exploratory laparotomy

**Predicted**: E

**Generated answer (first 300 chars)**:
> Answer: E…

**Top-2 retrieved snippets**:
1. [First_Aid_Step2.txt] eye response, five points for verbal response, and six points for motor response. Patients with chest trauma and shock may have cardiac tamponade. The relevant signs are JVD, hypotension, and mufﬂed heart sounds. This can be diagnosed with bedside ultrasound. If tamponade is diagnosed, an immediate …
2. [Surgery_Schwartz.txt] integrity of the proximal thoracic aorta. Unfortunately, these skilled examiners are rarely immediately available at all hours of the night, when many trauma patients present; there-fore, waiting for this test may result in inordinate delays. In addition, although both ultrasound techniques may demo…

---

## Error 5 — Model ignored context

**Question ID**: `medqa_test_23`

**Question**: A 62-year-old patient has been hospitalized for a week due to a stroke. One week into the hospitalization, he develops a fever and purulent cough. His vitals include: heart rate 88/min, respiratory rate 20/min, temperature 38.4°C (101.1°F), and blood pressure 110/85 mm Hg. On physical examination, he has basal crackles on the right side of the chest. Chest radiography shows a new consolidation on the same side. Complete blood count is as follows:
Hemoglobin 16 mg/dL
Hematocrit 50%
Leukocyte count 8,900/mm3
Neutrophils 72%
Bands 4%
Eosinophils 2%
Basophils 0%
Lymphocytes 17%
Monocytes 5%
Platelet count 280,000/mm3
What is the most likely causal microorganism?

**Options**: (A) Pseudomona aeruginosa | (B) Streptococcus pneumoniae | (C) Mycobacterium tuberculosis | (D) Haemophilus influenzae | (E) Staphylococcus aureus

**Correct**: (E) Staphylococcus aureus

**Predicted**: B

**Generated answer (first 300 chars)**:
> Answer: B…

**Top-2 retrieved snippets**:
1. [InternalMed_Harrison.txt] blood lactate level, respiratory alkalosis, or hypotension also should suggest the diagnosis. The systemic response can be quite variable, however. In one study, 36% of patients with severe sepsis had a normal temperature, 40% had a normal respiratory rate, 10% had a normal pulse rate, and 33% had n…
2. [InternalMed_Harrison.txt] and cardiomegaly and pulmonary edema on chest radiography. General laboratory studies are not specific. Mild to moderate normocytic anemia is common, but frank hemolysis and hemoglobinuria do not develop. Leukocyte counts are usually in the normal range or only slightly elevated, and leukopenia can …

---

## Error 6 — Retrieval miss

**Question ID**: `medqa_test_140`

**Question**: A 24-year-old pregnant woman at 28 weeks gestation presents to the emergency department with complaints of fever with chills and pain in her knee and ankle joints for the past 2 days. She also complains of headaches and difficulty moving her neck. Further questioning reveals that she had a tick bite on her arm while gardening a few days ago. Past medical history is noncontributory. She takes a multivitamin with iron and folate every day and has been receiving regular prenatal care and the pregnancy is progressing normally. On examination, an erythematous rash is seen on her right arm, as shown in the accompanying photograph. Her obstetric examination is normal. Ultrasound of the fetus is reassuring with a normal heartbeat and no gross abnormalities. A specimen is collected to test for Lyme disease. What is the next best step for this patient?

**Options**: (A) Ibuprofen | (B) Doxycycline | (C) Tetracycline | (D) Amoxicilin | (E) Gentamicin

**Correct**: (D) Amoxicilin

**Predicted**: B

**Generated answer (first 300 chars)**:
> Answer: B…

**Top-2 retrieved snippets**:
1. [Neurology_Adams.txt] development of an animal model by Pachner and colleagues suggests that there may be a chronic form of Borrelia infection. Lyme borreliosis has a worldwide distribution but the typical neurologic manifestations differ slightly in Europe and America, as emphasized in the review by Garcia-Monico and Be…
2. [First_Aid_Step1.txt] recurrent infections, no mature B cells Bruton disease (X-linked agammaglobulinemia) Recurrent cold (noninflamed) abscesses, eczema, high Hyper-IgE syndrome (Job syndrome: neutrophil 116 serum IgE,  eosinophils chemotaxis abnormality) “Strawberry tongue” Scarlet fever 136, Kawasaki disease 314 Abdo…

---

## Error 7 — Retrieval miss

**Question ID**: `medqa_test_1142`

**Question**: A 25-year-old female is brought to the emergency department by her family. They found her somnolent next to her computer and scattered pill bottles over two hours ago. The family cannot recall the types of pill bottles that they found and did not bring them to the ED. The patient's past medical history is notable for anxiety, obesity, hypertension, and polycystic ovarian syndrome. She is currently not on any medications other than an exercise program with which she is non-compliant. A physical exam is performed and is within normal limits. The patient begins communicating with the physician and states that she did take acetaminophen but it was only a few pills. Her temperature is 99.5°F (37.5°C), pulse is 82/min, blood pressure is 125/85 mmHg, respirations are 11/min, and oxygen saturation is 97% on room air. Which of the following is the next best step in management?

**Options**: (A) N-acetylcysteine | (B) Blood acetaminophen levels | (C) Charcoal | (D) IV fluids | (E) Syrup of ipecac

**Correct**: (A) N-acetylcysteine

**Predicted**: D

**Generated answer (first 300 chars)**:
> Answer: D…

**Top-2 retrieved snippets**:
1. [Pharmacology_Katzung.txt] mL Pregabalin (Lyrica) 1See https://www.deadiversion.usdoj.gov/schedules.2Emergency prescriptions may be telephoned if followed within 7 days by a valid written prescription annotated to indicate that it was previously placed by telephone. CMEA (Combat Methamphetamine Epidemic Act of 2005) establish…
2. [Gynecology_Novak.txt] regarding the need to discontinue any medications before surgery (e.g., aspirin, antiplatelet agents, diuretics, hormone replacement, or oral contraceptives), and those medications that should be continued (e.g., beta-blockers, α-2 agonists, statins, H2 blockers, and proton pump inhibitors). Collabo…

---

## Error 8 — Model ignored context

**Question ID**: `medqa_test_266`

**Question**: A 60-year-old man presents with a 2-day history of increasing difficulty in breathing with a productive cough. He reports having shortness of breath over the last 6 months, but he has felt worse since he contracted a cold that has been traveling around his office. Today, he reports body aches, headache, and fever along with this chronic cough. His past medical history is significant for prediabetes, which he controls with exercise and diet. He has a 30-pack-year smoking history. His blood pressure is 130/85 mmHg, pulse rate is 90/min, temperature is 36.9°C (98.5°F), and respiratory rate is 18/min. Physical examination reveals diminished breath sounds bilateral, a barrel-shaped chest, and measured breathing through pursed lips. A chest X-ray reveals a flattened diaphragm and no signs of consolidation. Pulmonary function testing reveals FEV1/FVC ratio of 60%. Arterial blood gases (ABG) of this patient are most likely to reveal which of the following?

**Options**: (A) Non-anion gap metabolic acidosis | (B) Primary respiratory acidosis | (C) Primary respiratory alkalosis | (D) Compensatory respiratory acidosis | (E) Anion gap metabolic acidosis with respiratory alkalosis

**Correct**: (B) Primary respiratory acidosis

**Predicted**: D

**Generated answer (first 300 chars)**:
> Answer: D…

**Top-2 retrieved snippets**:
1. [InternalMed_Harrison.txt] of the lung do not manifest as gas exchange abnormalities. As with the evaluation of most patients, the approach to a patient with disease of the respiratory system begins with a thorough history and a focused physical examination. Many patients will subsequently undergo pulmonary function testing, …
2. [InternalMed_Harrison.txt] engage and how these activities have changed over time. Dyspnea on exertion is often an early symptom of underlying lung or heart disease and warrants a thorough evaluation. Cough generally indicates disease of the respiratory system. The clinician should inquire about the duration of the cough, whe…

---

## Error 9 — Retrieval miss

**Question ID**: `medqa_test_1172`

**Question**: A four-day-old neonate is brought to the pediatrician with vaginal discharge for the last two days. Her mother is concerned about the blood-tinged discharge but states that her daughter has been feeding and voiding well. The neonate was delivered at 39 weeks gestation by an uncomplicated vaginal delivery, and she and her mother were discharged home after two days. The prenatal course was complicated by chlamydia in the mother during the first trimester, for which she and the partner were both treated with a negative test of cure. The neonate’s biological father is no longer involved the patient's care, but her mother’s boyfriend has been caring for the baby whenever the mother rests. At this visit, the neonate’s temperature is 98.5°F (36.9°C), pulse is 138/min, and respirations are 51/min. She appears comfortable, and cardiopulmonary and abdominal exams are unremarkable. There are no bruises or marks on her skin. Examination of the genitals reveals no vulvar irritation or skin changes, but there is scant pink mucoid discharge at the introitus. Which of the following is the best next step in management?

**Options**: (A) Vaginal exam under anesthesia | (B) Report to child protective services | (C) Vaginal culture | (D) Warm water irrigation of the vagina | (E) Reassurance

**Correct**: (E) Reassurance

**Predicted**: C

**Generated answer (first 300 chars)**:
> Answer: C: Vaginal culture…

**Top-2 retrieved snippets**:
1. [Obstentrics_Williams.txt] However, delayed postpartum uterine infection has been described by Hoyme and associates (1986). The syndrome, which develops 2 to 3 weeks postpartum, is distinct from early postpartum metritis. It is characterized by vaginal bleeding or discharge, low-grade fever, and uterine tenderness. Infection …
2. [InternalMed_Harrison.txt] frequency strongly suggests C. trachomatis urethritis. Other correlates of chlamydial urethral syndrome include a duration of dysuria of >7–10 days, lack of hematuria, and lack of suprapubic tenderness. Abnormal urethral Gram’s stains showing >10 PMNs per 1000× field in women with dysuria but withou…

---

## Error 10 — Model ignored context

**Question ID**: `medqa_test_946`

**Question**: A 49-year-old man comes to the physician because he has had multiple falls and multiple episodes of dizziness over the past 6 weeks. There is no personal or family history of serious illness. He drinks one pint of rum daily. He works as a foreman in a factory that produces industrial solvents. He is alert and oriented to time, place, and person. His temperature is 36.7°C (98.1°F), pulse is 88/min, and blood pressure is 108/70 mm Hg. Examination shows a wide-based gait. The patient is unable to stand with his feet together without support. There is a coarse tremor of the hands when he is asked to grab a pen. Muscle strength and tone are normal in all extremities. Sensation to pain, vibration, and position is intact bilaterally. Rapid alternating movements of the hands is impaired. Mental status examination shows no abnormalities. Which of the following is the most likely cause of this patient's condition?

**Options**: (A) Korsakoff syndrome | (B) Subacute combined degeneration | (C) Methanol poisoning | (D) Cerebellar degeneration | (E) Wernicke's encephalopathy

**Correct**: (D) Cerebellar degeneration

**Predicted**: E

**Generated answer (first 300 chars)**:
> Answer: E…

**Top-2 retrieved snippets**:
1. [Pharmacology_Katzung.txt] standing that is worse after meals and in hot environments. Symptoms started about 4 years ago and have slowly progressed to the point that he is disabled. He has fainted several times but always recovers conscious-ness almost as soon as he falls. Review of symptoms reveals slight worsening of const…
2. [Pharmacology_Katzung.txt] fiberoptic-assisted intubation) should be used to secure the airway. Pharmacologic Management of Parkinsonism & Other Movement Disorders Michael J. Aminoff, MD, DSc, FRCP A 76-year-old retired banker complains of a shuffling gait with occasional falls over the last year. He has developed a stooped p…

---
