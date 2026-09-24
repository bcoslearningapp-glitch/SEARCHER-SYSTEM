/** Lab and Map strings (en/fr/ar). Canonical enum codes are displayed as-is. */

export type LabStrings = {
  claims: string;
  newClaim: string;
  statement: string;
  claimType: string;
  important: string;
  strength: string;
  origin: string;
  assumptions: string;
  newAssumption: string;
  criticality: string;
  confirm: string;
  reject: string;
  hypotheses: string;
  newHypothesis: string;
  open: string;
  lifecycle: string;
  epistemic: string;
  suggested: string;
  counterEvidence: string;
  complete: string;
  incomplete: string;
  mechanisms: string;
  newMechanism: string;
  name: string;
  description: string;
  context: string;
  expectedOutcome: string;
  proposedMechanism: string;
  hypothesisAssumptions: string;
  boundaryConditions: string;
  falsification: string;
  changeReason: string;
  revise: string;
  advanceTo: string;
  reason: string;
  assess: string;
  evidenceMap: string;
  candidates: string;
  addEvidence: string;
  role: string;
  finding: string;
  excerpt: string;
  track: string;
  accept: string;
  independentOrigins: string;
  meaningfulConflict: string;
  searches: string;
  recordSearch: string;
  outcome: string;
  searchScope: string;
  searched: string;
  failed: string;
  notSearched: string;
  reference: string;
  standing: string;
  newReview: string;
  question: string;
  category: string;
  addEntry: string;
  layer: string;
  quranRef: string;
  judge: string;
  directness: string;
  reservation: string;
  rationale: string;
  history: string;
  noExcerpts: string;
  centralProblem: string;
  openQuestions: string;
  blockers: string;
  save: string;
  saving: string;
};

export const labEn: LabStrings = {
  claims: "Claims",
  newClaim: "Record a claim",
  statement: "Statement",
  claimType: "Claim type",
  important: "Important (requires counter-evidence search)",
  strength: "Evidence strength",
  origin: "Origin",
  assumptions: "Assumptions",
  newAssumption: "Record an assumption",
  criticality: "Criticality",
  confirm: "Confirm",
  reject: "Reject",
  hypotheses: "Hypotheses",
  newHypothesis: "Record a hypothesis",
  open: "Open",
  lifecycle: "Stage",
  epistemic: "Assessment",
  suggested: "Evidence suggests",
  counterEvidence: "Counter-evidence search",
  complete: "complete",
  incomplete: "not complete",
  mechanisms: "Mechanisms",
  newMechanism: "Record a mechanism",
  name: "Name",
  description: "Description",
  context: "Context",
  expectedOutcome: "Expected outcome",
  proposedMechanism: "Proposed mechanism",
  hypothesisAssumptions: "Assumptions",
  boundaryConditions: "Boundary conditions",
  falsification: "Falsification conditions",
  changeReason: "Reason for this change",
  revise: "Save new version",
  advanceTo: "Move to stage",
  reason: "Reason",
  assess: "Record assessment",
  evidenceMap: "Evidence map",
  candidates: "Candidates awaiting your assessment",
  addEvidence: "Add evidence",
  role: "Role",
  finding: "What the passage shows",
  excerpt: "Source passage",
  track: "Search track",
  accept: "Accept",
  independentOrigins: "Independent origins",
  meaningfulConflict: "Meaningful conflict between nontrivial evidence",
  searches: "Searches",
  recordSearch: "Record a search",
  outcome: "Outcome",
  searchScope: "What was searched",
  searched: "searched",
  failed: "search failed",
  notSearched: "not searched",
  reference: "Reference review",
  standing: "Standing",
  newReview: "Start a reference review",
  question: "Question",
  category: "Analytical category",
  addEntry: "Add layer",
  layer: "Layer",
  quranRef: "Qur'an reference (surah:ayah)",
  judge: "Record judgment",
  directness: "Directness",
  reservation: "Reservation",
  rationale: "Rationale",
  history: "Version history",
  noExcerpts: "No source passages yet. Obtain one through the project's sources.",
  centralProblem: "Central problem",
  openQuestions: "Open questions",
  blockers: "Blocking issues",
  save: "Save",
  saving: "Saving…",
};

export const labFr: LabStrings = {
  claims: "Affirmations",
  newClaim: "Enregistrer une affirmation",
  statement: "Énoncé",
  claimType: "Type d'affirmation",
  important: "Importante (recherche de contre-preuves requise)",
  strength: "Force des preuves",
  origin: "Origine",
  assumptions: "Présupposés",
  newAssumption: "Enregistrer un présupposé",
  criticality: "Criticité",
  confirm: "Confirmer",
  reject: "Rejeter",
  hypotheses: "Hypothèses",
  newHypothesis: "Enregistrer une hypothèse",
  open: "Ouvrir",
  lifecycle: "Étape",
  epistemic: "Évaluation",
  suggested: "Les preuves suggèrent",
  counterEvidence: "Recherche de contre-preuves",
  complete: "terminée",
  incomplete: "non terminée",
  mechanisms: "Mécanismes",
  newMechanism: "Enregistrer un mécanisme",
  name: "Nom",
  description: "Description détaillée",
  context: "Contexte",
  expectedOutcome: "Résultat attendu",
  proposedMechanism: "Mécanisme proposé",
  hypothesisAssumptions: "Présupposés",
  boundaryConditions: "Conditions limites",
  falsification: "Conditions de réfutation",
  changeReason: "Raison de la modification",
  revise: "Enregistrer une nouvelle version",
  advanceTo: "Passer à l'étape",
  reason: "Motif",
  assess: "Enregistrer l'évaluation",
  evidenceMap: "Carte des preuves",
  candidates: "Candidats en attente de votre évaluation",
  addEvidence: "Ajouter une preuve",
  role: "Rôle",
  finding: "Ce que montre le passage",
  excerpt: "Passage source",
  track: "Piste de recherche",
  accept: "Accepter",
  independentOrigins: "Origines indépendantes",
  meaningfulConflict: "Conflit significatif entre preuves non négligeables",
  searches: "Recherches",
  recordSearch: "Enregistrer une recherche",
  outcome: "Résultat",
  searchScope: "Ce qui a été recherché",
  searched: "recherchée",
  failed: "échec de la recherche",
  notSearched: "non recherchée",
  reference: "Examen de référence",
  standing: "Situation",
  newReview: "Commencer un examen de référence",
  question: "Question posée",
  category: "Catégorie analytique",
  addEntry: "Ajouter une couche",
  layer: "Couche",
  quranRef: "Référence coranique (sourate:verset)",
  judge: "Enregistrer le jugement",
  directness: "Degré de lien direct",
  reservation: "Réserve",
  rationale: "Justification",
  history: "Historique des versions",
  noExcerpts: "Aucun passage source. Obtenez-en un via les sources du projet.",
  centralProblem: "Problème central",
  openQuestions: "Questions ouvertes",
  blockers: "Blocages",
  save: "Enregistrer",
  saving: "Enregistrement…",
};

export const labAr: LabStrings = {
  claims: "الادعاءات",
  newClaim: "تسجيل ادعاء",
  statement: "النص",
  claimType: "نوع الادعاء",
  important: "مهم (يتطلب البحث عن أدلة مضادة)",
  strength: "قوة الأدلة",
  origin: "المصدر",
  assumptions: "الافتراضات",
  newAssumption: "تسجيل افتراض",
  criticality: "درجة الأهمية",
  confirm: "تأكيد",
  reject: "رفض",
  hypotheses: "الفرضيات",
  newHypothesis: "تسجيل فرضية",
  open: "فتح",
  lifecycle: "المرحلة",
  epistemic: "التقييم",
  suggested: "ما تشير إليه الأدلة",
  counterEvidence: "البحث عن الأدلة المضادة",
  complete: "مكتمل",
  incomplete: "غير مكتمل",
  mechanisms: "الآليات",
  newMechanism: "تسجيل آلية",
  name: "الاسم",
  description: "الوصف",
  context: "السياق",
  expectedOutcome: "النتيجة المتوقعة",
  proposedMechanism: "الآلية المقترحة",
  hypothesisAssumptions: "الافتراضات المسبقة",
  boundaryConditions: "شروط الحدود",
  falsification: "شروط الدحض",
  changeReason: "سبب هذا التغيير",
  revise: "حفظ إصدار جديد",
  advanceTo: "الانتقال إلى المرحلة",
  reason: "السبب",
  assess: "تسجيل التقييم",
  evidenceMap: "خريطة الأدلة",
  candidates: "أدلة مرشحة بانتظار تقييمك",
  addEvidence: "إضافة دليل",
  role: "الدور",
  finding: "ما يُظهره المقطع",
  excerpt: "مقطع المصدر",
  track: "مسار البحث",
  accept: "قبول",
  independentOrigins: "أصول مستقلة",
  meaningfulConflict: "تعارض معتبر بين أدلة غير هامشية",
  searches: "عمليات البحث",
  recordSearch: "تسجيل عملية بحث",
  outcome: "النتيجة",
  searchScope: "نطاق البحث",
  searched: "تم البحث",
  failed: "فشل البحث",
  notSearched: "لم يُبحث",
  reference: "المراجعة المرجعية",
  standing: "الوضع",
  newReview: "بدء مراجعة مرجعية",
  question: "المسألة",
  category: "الفئة التحليلية",
  addEntry: "إضافة طبقة",
  layer: "الطبقة",
  quranRef: "المرجع القرآني (سورة:آية)",
  judge: "تسجيل الحكم",
  directness: "درجة المباشرة",
  reservation: "التحفظ",
  rationale: "التعليل",
  history: "سجل الإصدارات",
  noExcerpts: "لا توجد مقاطع مصدرية بعد. احصل عليها من مصادر المشروع.",
  centralProblem: "المشكلة المركزية",
  openQuestions: "أسئلة مفتوحة",
  blockers: "العوائق",
  save: "حفظ",
  saving: "جارٍ الحفظ…",
};
