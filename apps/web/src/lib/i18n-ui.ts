/** Workflow UI strings for en/fr/ar. Canonical enum codes are shown as-is (they are portable vocabulary). */

export type UiStrings = {
  projects: string;
  newProject: string;
  title: string;
  initialInput: string;
  initialInputHint: string;
  inputType: string;
  sensitivity: string;
  riskLevel: string;
  create: string;
  creating: string;
  noProjects: string;
  status: string;
  mode: string;
  researchState: string;
  currentQuestion: string;
  nextAction: string;
  why: string;
  unresolved: string;
  findings: string;
  none: string;
  attention: string;
  nothingNeedsAttention: string;
  problemFrame: string;
  frameHistory: string;
  saveDraft: string;
  saving: string;
  saved: string;
  approve: string;
  approving: string;
  approvedMessage: string;
  acknowledgeReservations: string;
  approvalReason: string;
  approvalExplainer: string;
  listHint: string;
  frameFields: Record<
    | "central_issue"
    | "current_state"
    | "desired_state"
    | "gap"
    | "context"
    | "readiness"
    | "current_explanations"
    | "initial_hypotheses"
    | "constraints"
    | "known"
    | "unknowns"
    | "research_questions"
    | "reference_review_points",
    string
  >;
  notes: string;
  notesExplainer: string;
  noteBody: string;
  add: string;
  adding: string;
  capture: string;
  captureAs: Record<"current_question" | "unresolved_item" | "established_finding", string>;
  captured: string;
  decisions: string;
  question: string;
  options: string;
  optionsHint: string;
  blocking: string;
  createDecision: string;
  resolve: string;
  finalDecision: string;
  justification: string;
  aiRecommendation: string;
  library: string;
  catalogSource: string;
  workTitle: string;
  authors: string;
  authorityLayer: string;
  editionLabel: string;
  language: string;
  publisher: string;
  holding: string;
  holdingNone: string;
  holdingPhysical: string;
  holdingRestricted: string;
  holdingNote: string;
  catalog: string;
  cataloging: string;
  upload: string;
  chooseFile: string;
  uploading: string;
  uploaded: string;
  verification: string;
  available: string;
  unavailable: string;
  ingestion: string;
  search: string;
  searchPlaceholder: string;
  searching: string;
  noResults: string;
  searchedScope: string;
  page: string;
  discoveryOnly: string;
  sources: string;
  accessRequests: string;
  requestAccess: string;
  requesting: string;
  reason: string;
  scope: string;
  acceptableForms: string;
  priority: string;
  respond: string;
  responseForm: string;
  location: string;
  excerptText: string;
  fulfills: string;
  excerpts: string;
  linkToProject: string;
  linking: string;
  addToProject: string;
  edition: string;
  noSources: string;
  moveTo: string;
  back: string;
  loadError: string;
};

export const en: UiStrings = {
  projects: "Projects",
  newProject: "New project",
  title: "Provisional title",
  initialInput: "Initial question, problem, idea or system",
  initialInputHint: "Raw input is a starting point; it will be clarified before it becomes a Problem Frame.",
  inputType: "Input type",
  sensitivity: "Sensitivity",
  riskLevel: "Risk level",
  create: "Create project",
  creating: "Creating…",
  noProjects: "No projects yet. Start one with a question, problem or idea.",
  status: "Status",
  mode: "Mode",
  researchState: "Research state",
  currentQuestion: "Current question",
  nextAction: "Next step",
  why: "Why",
  unresolved: "Unresolved",
  findings: "Established findings",
  none: "None yet",
  attention: "Needs your attention",
  nothingNeedsAttention: "Nothing needs your attention.",
  problemFrame: "Problem Frame",
  frameHistory: "Version history",
  saveDraft: "Save draft",
  saving: "Saving…",
  saved: "Saved.",
  approve: "Approve as baseline",
  approving: "Approving…",
  approvedMessage: "Approved.",
  acknowledgeReservations: "I acknowledge the Framing Gate reservations",
  approvalReason: "Reason (required when overriding reservations)",
  approvalExplainer: "Approval is an explicit decision. It is never inferred from conversation.",
  listHint: "One item per line",
  frameFields: {
    central_issue: "Central issue",
    current_state: "Current state (what is happening)",
    desired_state: "Desired state",
    gap: "Gap",
    context: "Context",
    readiness: "Readiness notes",
    current_explanations: "Current explanations",
    initial_hypotheses: "Initial hypotheses",
    constraints: "Constraints",
    known: "What is known",
    unknowns: "What is unknown",
    research_questions: "Research questions",
    reference_review_points: "Points requiring reference review",
  },
  notes: "Scratch notes",
  notesExplainer: "Informal thinking. Nothing here becomes formal knowledge unless you capture it.",
  noteBody: "Note",
  add: "Add",
  adding: "Adding…",
  capture: "Capture",
  captureAs: {
    current_question: "as current question",
    unresolved_item: "as unresolved item",
    established_finding: "as established finding",
  },
  captured: "Captured",
  decisions: "Decisions",
  question: "Question",
  options: "Options",
  optionsHint: "At least two, one per line",
  blocking: "Blocking",
  createDecision: "Record decision question",
  resolve: "Decide",
  finalDecision: "Decision",
  justification: "Justification",
  aiRecommendation: "AI recommendation (not a decision)",
  library: "Library",
  catalogSource: "Catalog a source",
  workTitle: "Work title",
  authors: "Authors (separate with ;)",
  authorityLayer: "Authority layer",
  editionLabel: "Edition / translation",
  language: "Language",
  publisher: "Publisher",
  holding: "Holding",
  holdingNone: "Metadata only (no copy)",
  holdingPhysical: "Physical copy",
  holdingRestricted: "Restricted access",
  holdingNote: "Holding note",
  catalog: "Catalog",
  cataloging: "Cataloging…",
  upload: "Upload file",
  chooseFile: "File to upload",
  uploading: "Uploading…",
  uploaded: "Uploaded.",
  verification: "Verification",
  available: "Available here",
  unavailable: "Not available here",
  ingestion: "Text extraction",
  search: "Search the library",
  searchPlaceholder: "Words to find in ingested sources",
  searching: "Searching…",
  noResults: "No relevant passages found",
  searchedScope: "Searched",
  page: "p.",
  discoveryOnly: "Search results are discovery aids, not quotations.",
  sources: "Sources",
  accessRequests: "Source access requests",
  requestAccess: "Request access",
  requesting: "Requesting…",
  reason: "Why it is needed",
  scope: "Pages, chapter or section",
  acceptableForms: "Acceptable responses",
  priority: "Priority",
  respond: "Provide content",
  responseForm: "Response type",
  location: "Location (page, section)",
  excerptText: "Text",
  fulfills: "This completes the request",
  excerpts: "Supplied content",
  linkToProject: "Project",
  linking: "Adding…",
  addToProject: "Add to project",
  edition: "Edition",
  noSources: "No sources yet.",
  moveTo: "Move project to",
  back: "Back",
  loadError: "The research service could not be reached. Your data is safe; try again shortly.",
};

export const fr: UiStrings = {
  ...en,
  projects: "Projets",
  newProject: "Nouveau projet",
  title: "Titre provisoire",
  initialInput: "Question, problème, idée ou système initial",
  initialInputHint: "L'entrée brute est un point de départ ; elle sera clarifiée avant de devenir un cadrage.",
  inputType: "Type d'entrée",
  sensitivity: "Sensibilité",
  riskLevel: "Niveau de risque",
  create: "Créer le projet",
  creating: "Création…",
  noProjects: "Aucun projet. Commencez par une question, un problème ou une idée.",
  status: "Statut",
  mode: "Mode",
  researchState: "État de la recherche",
  currentQuestion: "Question actuelle",
  nextAction: "Prochaine étape",
  why: "Pourquoi",
  unresolved: "Non résolu",
  findings: "Résultats établis",
  none: "Rien pour l'instant",
  attention: "Requiert votre attention",
  nothingNeedsAttention: "Rien ne requiert votre attention.",
  problemFrame: "Cadrage du problème",
  frameHistory: "Historique des versions",
  saveDraft: "Enregistrer le brouillon",
  saving: "Enregistrement…",
  saved: "Enregistré.",
  approve: "Approuver comme référence",
  approving: "Approbation…",
  approvedMessage: "Approuvé.",
  acknowledgeReservations: "Je prends acte des réserves du contrôle de cadrage",
  approvalReason: "Motif (obligatoire en cas de dérogation)",
  approvalExplainer: "L'approbation est une décision explicite ; elle n'est jamais déduite de la conversation.",
  listHint: "Un élément par ligne",
  frameFields: {
    central_issue: "Enjeu central",
    current_state: "Situation actuelle",
    desired_state: "Situation souhaitée",
    gap: "Écart",
    context: "Contexte",
    readiness: "Notes de préparation",
    current_explanations: "Explications actuelles",
    initial_hypotheses: "Hypothèses initiales",
    constraints: "Contraintes",
    known: "Ce qui est connu",
    unknowns: "Ce qui est inconnu",
    research_questions: "Questions de recherche",
    reference_review_points: "Points nécessitant un examen de référence",
  },
  notes: "Notes libres",
  notesExplainer: "Réflexion informelle. Rien ne devient connaissance formelle sans capture explicite.",
  noteBody: "Note",
  add: "Ajouter",
  adding: "Ajout…",
  capture: "Capturer",
  captureAs: {
    current_question: "comme question actuelle",
    unresolved_item: "comme point non résolu",
    established_finding: "comme résultat établi",
  },
  captured: "Capturée",
  decisions: "Décisions",
  question: "Question",
  options: "Options",
  optionsHint: "Au moins deux, une par ligne",
  blocking: "Bloquante",
  createDecision: "Enregistrer la question",
  resolve: "Décider",
  finalDecision: "Décision",
  justification: "Justification",
  aiRecommendation: "Recommandation de l'IA (pas une décision)",
  library: "Bibliothèque",
  catalogSource: "Cataloguer une source",
  workTitle: "Titre de l'œuvre",
  authors: "Auteurs (séparés par ;)",
  authorityLayer: "Niveau d'autorité",
  editionLabel: "Édition / traduction",
  language: "Langue",
  publisher: "Éditeur",
  holding: "Exemplaire",
  holdingNone: "Métadonnées seules",
  holdingPhysical: "Exemplaire physique",
  holdingRestricted: "Accès restreint",
  holdingNote: "Note sur l'exemplaire",
  catalog: "Cataloguer",
  cataloging: "Catalogage…",
  upload: "Téléverser un fichier",
  chooseFile: "Fichier à téléverser",
  uploading: "Téléversement…",
  uploaded: "Téléversé.",
  verification: "Vérification",
  available: "Disponible ici",
  unavailable: "Non disponible ici",
  ingestion: "Extraction du texte",
  search: "Rechercher dans la bibliothèque",
  searchPlaceholder: "Mots à trouver dans les sources",
  searching: "Recherche…",
  noResults: "Aucun passage pertinent trouvé",
  searchedScope: "Recherché dans",
  page: "p.",
  discoveryOnly: "Les résultats aident à découvrir ; ce ne sont pas des citations.",
  sources: "Sources",
  accessRequests: "Demandes d'accès aux sources",
  requestAccess: "Demander l'accès",
  requesting: "Demande…",
  reason: "Pourquoi c'est nécessaire",
  scope: "Pages, chapitre ou section",
  acceptableForms: "Réponses acceptées",
  priority: "Priorité",
  respond: "Fournir le contenu",
  responseForm: "Type de réponse",
  location: "Emplacement (page, section)",
  excerptText: "Texte",
  fulfills: "Ceci complète la demande",
  excerpts: "Contenu fourni",
  linkToProject: "Projet",
  linking: "Ajout…",
  addToProject: "Ajouter au projet",
  edition: "Édition",
  noSources: "Aucune source.",
  moveTo: "Passer le projet à",
  back: "Retour",
  loadError: "Le service de recherche est injoignable. Vos données sont intactes ; réessayez bientôt.",
};

export const ar: UiStrings = {
  ...en,
  projects: "المشاريع",
  newProject: "مشروع جديد",
  title: "عنوان مبدئي",
  initialInput: "السؤال أو المشكلة أو الفكرة أو النظام الأولي",
  initialInputHint: "المدخل الخام نقطة بداية، وسيُوضَّح قبل أن يصبح إطارًا للمشكلة.",
  inputType: "نوع المدخل",
  sensitivity: "درجة الحساسية",
  riskLevel: "مستوى المخاطرة",
  create: "إنشاء المشروع",
  creating: "جارٍ الإنشاء…",
  noProjects: "لا توجد مشاريع بعد. ابدأ بسؤال أو مشكلة أو فكرة.",
  status: "الحالة",
  mode: "النمط",
  researchState: "حالة البحث",
  currentQuestion: "السؤال الحالي",
  nextAction: "الخطوة التالية",
  why: "السبب",
  unresolved: "مسائل غير محسومة",
  findings: "نتائج ثابتة",
  none: "لا شيء بعد",
  attention: "يحتاج إلى انتباهك",
  nothingNeedsAttention: "لا شيء يحتاج إلى انتباهك.",
  problemFrame: "إطار المشكلة",
  frameHistory: "سجل الإصدارات",
  saveDraft: "حفظ المسودة",
  saving: "جارٍ الحفظ…",
  saved: "تم الحفظ.",
  approve: "اعتماد كخط أساس",
  approving: "جارٍ الاعتماد…",
  approvedMessage: "تم الاعتماد.",
  acknowledgeReservations: "أُقِرّ بتحفظات بوابة التأطير",
  approvalReason: "السبب (مطلوب عند تجاوز التحفظات)",
  approvalExplainer: "الاعتماد قرار صريح، ولا يُستنتج من المحادثة أبدًا.",
  listHint: "عنصر واحد في كل سطر",
  frameFields: {
    central_issue: "القضية المركزية",
    current_state: "الواقع الحالي",
    desired_state: "الحالة المنشودة",
    gap: "الفجوة",
    context: "السياق",
    readiness: "ملاحظات الجاهزية",
    current_explanations: "التفسيرات الحالية",
    initial_hypotheses: "الفرضيات الأولية",
    constraints: "القيود",
    known: "المعلوم",
    unknowns: "المجهول",
    research_questions: "أسئلة البحث",
    reference_review_points: "نقاط تحتاج إلى مراجعة مرجعية",
  },
  notes: "ملاحظات حرة",
  notesExplainer: "تفكير غير رسمي. لا يصبح شيء هنا معرفة رسمية إلا إذا التقطته صراحةً.",
  noteBody: "ملاحظة",
  add: "إضافة",
  adding: "جارٍ الإضافة…",
  capture: "التقاط",
  captureAs: {
    current_question: "كسؤال حالي",
    unresolved_item: "كمسألة غير محسومة",
    established_finding: "كنتيجة ثابتة",
  },
  captured: "مُلتقَطة",
  decisions: "القرارات",
  question: "السؤال",
  options: "الخيارات",
  optionsHint: "خياران على الأقل، واحد في كل سطر",
  blocking: "معيق",
  createDecision: "تسجيل سؤال القرار",
  resolve: "قرّر",
  finalDecision: "القرار",
  justification: "المسوّغ",
  aiRecommendation: "توصية الذكاء الاصطناعي (ليست قرارًا)",
  library: "المكتبة",
  catalogSource: "فهرسة مصدر",
  workTitle: "عنوان العمل",
  authors: "المؤلفون (افصل بـ ;)",
  authorityLayer: "طبقة المرجعية",
  editionLabel: "الطبعة / الترجمة",
  language: "اللغة",
  publisher: "الناشر",
  holding: "النسخة",
  holdingNone: "بيانات وصفية فقط",
  holdingPhysical: "نسخة ورقية",
  holdingRestricted: "وصول مقيد",
  holdingNote: "ملاحظة عن النسخة",
  catalog: "فهرسة",
  cataloging: "جارٍ الفهرسة…",
  upload: "رفع ملف",
  chooseFile: "الملف المراد رفعه",
  uploading: "جارٍ الرفع…",
  uploaded: "تم الرفع.",
  verification: "التحقق",
  available: "متاح هنا",
  unavailable: "غير متاح هنا",
  ingestion: "استخراج النص",
  search: "البحث في المكتبة",
  searchPlaceholder: "كلمات للبحث عنها في المصادر",
  searching: "جارٍ البحث…",
  noResults: "لم يُعثر على مقاطع ذات صلة",
  searchedScope: "نطاق البحث",
  page: "ص",
  discoveryOnly: "نتائج البحث وسائل استكشاف وليست اقتباسات.",
  sources: "المصادر",
  accessRequests: "طلبات الوصول إلى المصادر",
  requestAccess: "طلب وصول",
  requesting: "جارٍ الطلب…",
  reason: "سبب الحاجة",
  scope: "الصفحات أو الفصل أو القسم",
  acceptableForms: "الردود المقبولة",
  priority: "الأولوية",
  respond: "تقديم المحتوى",
  responseForm: "نوع الرد",
  location: "الموضع (صفحة، قسم)",
  excerptText: "النص",
  fulfills: "هذا يستوفي الطلب",
  excerpts: "المحتوى المقدَّم",
  linkToProject: "المشروع",
  linking: "جارٍ الإضافة…",
  addToProject: "إضافة إلى المشروع",
  edition: "الطبعة",
  noSources: "لا توجد مصادر بعد.",
  moveTo: "نقل المشروع إلى",
  back: "رجوع",
  loadError: "تعذّر الوصول إلى خدمة البحث. بياناتك سليمة؛ حاول مجددًا بعد قليل.",
};
