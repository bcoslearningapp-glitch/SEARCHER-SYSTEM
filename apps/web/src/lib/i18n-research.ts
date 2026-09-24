/** Research planning strings (en/fr/ar). Canonical enum codes are displayed as-is. */

export type ResearchStrings = {
  tab: string;
  plans: string;
  noPlans: string;
  newPlan: string;
  question: string;
  decisionServed: string;
  questionType: string;
  riskImpact: string;
  evidenceTypes: string;
  languages: string;
  languagesHint: string;
  trackApproach: Record<"SUPPORT" | "CHALLENGE" | "ALTERNATIVE_EXPLANATION", string>;
  sufficiencyCriteria: string;
  maxWebSearches: string;
  create: string;
  creating: string;
  version: string;
  coverage: string;
  searched: string;
  notSearched: string;
  failed: string;
  searches: string;
  noSearches: string;
  localSearch: string;
  localExplainer: string;
  track: string;
  queries: string;
  queriesHint: string;
  search: string;
  searching: string;
  webSearch: string;
  webExplainer: string;
  webUsed: string;
  leads: string;
  noLeads: string;
  sufficiency: string;
  sufficiencyExplainer: string;
  result: string;
  considerations: Record<string, string>;
  rationale: string;
  recommendExperiment: string;
  record: string;
  current: string;
  history: string;
};

const considerationsEn = {
  support_evidence: "Support evidence",
  counter_evidence: "Counter-evidence",
  alternative_explanations: "Alternative explanations",
  independence: "Evidence independence",
  diversity: "Evidence diversity",
  context_fit: "Context fit",
  critical_unknowns: "Critical unknowns",
  impact: "Impact",
  reversibility: "Reversibility",
  remaining_uncertainty: "Remaining uncertainty",
};

export const researchEn: ResearchStrings = {
  tab: "Research",
  plans: "Research plans",
  noPlans: "No research plan yet. Start with an explicit question.",
  newPlan: "New research plan",
  question: "Research question",
  decisionServed: "Decision or use the answer serves",
  questionType: "Question type",
  riskImpact: "Risk / impact",
  evidenceTypes: "Desired evidence types",
  languages: "Research languages",
  languagesHint: "Codes such as en, fr, ar — one per line",
  trackApproach: {
    SUPPORT: "Support track approach",
    CHALLENGE: "Challenge track approach",
    ALTERNATIVE_EXPLANATION: "Alternative-explanation track approach",
  },
  sufficiencyCriteria: "Sufficiency criteria",
  maxWebSearches: "Web search budget (queries)",
  create: "Create plan",
  creating: "Creating…",
  version: "Version",
  coverage: "Track coverage",
  searched: "searched",
  notSearched: "not searched",
  failed: "search failed",
  searches: "Search log",
  noSearches: "No searches recorded yet.",
  localSearch: "Search the project library",
  localExplainer: "The project library is searched before any external research. Every search is logged.",
  track: "Track",
  queries: "Queries",
  queriesHint: "One per line",
  search: "Search",
  searching: "Searching…",
  webSearch: "Web search",
  webExplainer: "Results arrive as source leads to catalogue and verify — never as evidence.",
  webUsed: "Web queries used",
  leads: "Web leads",
  noLeads: "No web leads yet.",
  sufficiency: "Sufficiency",
  sufficiencyExplainer:
    "Your judgment, relative to the decision this plan serves. “Not known” is a valid conclusion. Sufficiently answered needs the challenge and alternative tracks searched.",
  result: "Conclusion",
  considerations: considerationsEn,
  rationale: "Rationale",
  recommendExperiment: "Further reading has low value; recommend a controlled experiment",
  record: "Record assessment",
  current: "Current",
  history: "History",
};

export const researchFr: ResearchStrings = {
  tab: "Recherche",
  plans: "Plans de recherche",
  noPlans: "Aucun plan de recherche. Commencez par une question explicite.",
  newPlan: "Nouveau plan de recherche",
  question: "Question de recherche",
  decisionServed: "Décision ou usage que sert la réponse",
  questionType: "Type de question",
  riskImpact: "Risque / impact",
  evidenceTypes: "Types de preuves recherchés",
  languages: "Langues de recherche",
  languagesHint: "Codes comme en, fr, ar — un par ligne",
  trackApproach: {
    SUPPORT: "Approche de la piste de soutien",
    CHALLENGE: "Approche de la piste de contestation",
    ALTERNATIVE_EXPLANATION: "Approche de la piste des explications alternatives",
  },
  sufficiencyCriteria: "Critères de suffisance",
  maxWebSearches: "Budget de recherche web (requêtes)",
  create: "Créer le plan",
  creating: "Création…",
  version: "Version",
  coverage: "Couverture des pistes",
  searched: "recherchée",
  notSearched: "non recherchée",
  failed: "échec de la recherche",
  searches: "Journal des recherches",
  noSearches: "Aucune recherche enregistrée.",
  localSearch: "Chercher dans la bibliothèque du projet",
  localExplainer: "La bibliothèque du projet est consultée avant toute recherche externe. Chaque recherche est journalisée.",
  track: "Piste",
  queries: "Requêtes",
  queriesHint: "Une par ligne",
  search: "Chercher",
  searching: "Recherche…",
  webSearch: "Recherche web",
  webExplainer: "Les résultats arrivent comme pistes de sources à cataloguer et vérifier — jamais comme preuves.",
  webUsed: "Requêtes web utilisées",
  leads: "Pistes web",
  noLeads: "Aucune piste web.",
  sufficiency: "Suffisance",
  sufficiencyExplainer:
    "Votre jugement, relatif à la décision que sert ce plan. « Inconnu » est une conclusion valide. « Suffisamment répondu » exige que les pistes de contestation et d'alternatives aient été recherchées.",
  result: "Conclusion",
  considerations: {
    support_evidence: "Preuves de soutien",
    counter_evidence: "Contre-preuves",
    alternative_explanations: "Explications alternatives",
    independence: "Indépendance des preuves",
    diversity: "Diversité des preuves",
    context_fit: "Adéquation au contexte",
    critical_unknowns: "Inconnues critiques",
    impact: "Impact",
    reversibility: "Réversibilité",
    remaining_uncertainty: "Incertitude restante",
  },
  rationale: "Justification",
  recommendExperiment: "La lecture supplémentaire apporte peu ; recommander une expérience contrôlée",
  record: "Enregistrer l'évaluation",
  current: "Actuelle",
  history: "Historique",
};

export const researchAr: ResearchStrings = {
  tab: "البحث",
  plans: "خطط البحث",
  noPlans: "لا توجد خطة بحث بعد. ابدأ بسؤال صريح.",
  newPlan: "خطة بحث جديدة",
  question: "سؤال البحث",
  decisionServed: "القرار أو الاستخدام الذي تخدمه الإجابة",
  questionType: "نوع السؤال",
  riskImpact: "المخاطرة / الأثر",
  evidenceTypes: "أنواع الأدلة المطلوبة",
  languages: "لغات البحث",
  languagesHint: "رموز مثل en وfr وar — رمز في كل سطر",
  trackApproach: {
    SUPPORT: "منهج مسار التأييد",
    CHALLENGE: "منهج مسار الاعتراض",
    ALTERNATIVE_EXPLANATION: "منهج مسار التفسيرات البديلة",
  },
  sufficiencyCriteria: "معايير الكفاية",
  maxWebSearches: "ميزانية البحث على الويب (استعلامات)",
  create: "إنشاء الخطة",
  creating: "جارٍ الإنشاء…",
  version: "الإصدار",
  coverage: "تغطية المسارات",
  searched: "تم البحث",
  notSearched: "لم يُبحث",
  failed: "فشل البحث",
  searches: "سجل البحث",
  noSearches: "لا توجد عمليات بحث مسجلة بعد.",
  localSearch: "البحث في مكتبة المشروع",
  localExplainer: "يُبحث في مكتبة المشروع قبل أي بحث خارجي. وتُسجَّل كل عملية بحث.",
  track: "المسار",
  queries: "الاستعلامات",
  queriesHint: "استعلام في كل سطر",
  search: "ابحث",
  searching: "جارٍ البحث…",
  webSearch: "البحث على الويب",
  webExplainer: "تصل النتائج كمصادر محتملة للفهرسة والتحقق — وليست أدلة أبداً.",
  webUsed: "استعلامات الويب المستخدمة",
  leads: "مصادر محتملة من الويب",
  noLeads: "لا توجد مصادر محتملة بعد.",
  sufficiency: "الكفاية",
  sufficiencyExplainer:
    "حكمك أنت، بالنسبة إلى القرار الذي تخدمه هذه الخطة. «غير معروف» استنتاج مقبول. ولا يصح «أُجيب بما يكفي» إلا بعد البحث في مساري الاعتراض والتفسيرات البديلة.",
  result: "الاستنتاج",
  considerations: {
    support_evidence: "أدلة التأييد",
    counter_evidence: "الأدلة المضادة",
    alternative_explanations: "التفسيرات البديلة",
    independence: "استقلال الأدلة",
    diversity: "تنوع الأدلة",
    context_fit: "ملاءمة السياق",
    critical_unknowns: "المجهولات الحرجة",
    impact: "الأثر",
    reversibility: "قابلية التراجع",
    remaining_uncertainty: "عدم اليقين المتبقي",
  },
  rationale: "المسوّغ",
  recommendExperiment: "قيمة القراءة الإضافية منخفضة؛ يُوصى بتجربة مضبوطة",
  record: "تسجيل التقييم",
  current: "الحالي",
  history: "السجل",
};
