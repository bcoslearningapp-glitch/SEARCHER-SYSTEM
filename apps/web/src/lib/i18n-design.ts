/** Design synthesis strings (en/fr/ar). Canonical enum codes are displayed as-is. */

export type DesignStrings = {
  tab: string;
  requirements: string;
  requirementsExplainer: string;
  noRequirements: string;
  newRequirement: string;
  statement: string;
  priority: string;
  basis: string;
  traceNote: string;
  addRequirement: string;
  confirm: string;
  withdraw: string;
  withdrawReason: string;
  proposedByAI: string;
  version: string;
  concepts: string;
  conceptsExplainer: string;
  noConcepts: string;
  newConcept: string;
  title: string;
  description: string;
  origin: string;
  originReference: string;
  hypotheses: string;
  mechanisms: string;
  derivedFrom: string;
  addConcept: string;
  coverage: string;
  stale: string;
  recordCoverage: string;
  note: string;
  readiness: string;
  evaluate: string;
  notEvaluated: string;
  select: string;
  selectExplainer: string;
  reason: string;
  acknowledge: string;
  reject: string;
  ground: string;
  reusableMechanisms: string;
  rejectedBecause: string;
  saving: string;
};

export const designEn: DesignStrings = {
  tab: "Design",
  requirements: "Design requirements",
  requirementsExplainer:
    "Requirements come before solutions. Each is traced to what it derives from; a revision keeps the earlier version.",
  noRequirements: "No design requirements yet. A concept cannot be selected until there are some.",
  newRequirement: "New requirement",
  statement: "Statement",
  priority: "Priority",
  basis: "Derived from",
  traceNote: "Trace note",
  addRequirement: "Add requirement",
  confirm: "Confirm",
  withdraw: "Withdraw",
  withdrawReason: "Reason for withdrawal",
  proposedByAI: "Proposed by AI — needs confirmation",
  version: "Version",
  concepts: "Design concepts",
  conceptsExplainer:
    "Concepts keep their origin. Selection is your decision after the Design Readiness Gate; rejected concepts stay in history.",
  noConcepts: "No design concepts yet.",
  newConcept: "New concept",
  title: "Title",
  description: "Description",
  origin: "Origin",
  originReference: "Origin reference",
  hypotheses: "Hypotheses it builds on",
  mechanisms: "Mechanisms",
  derivedFrom: "Derived from concepts",
  addConcept: "Add concept",
  coverage: "Requirement coverage",
  stale: "judged against an earlier version",
  recordCoverage: "Record coverage",
  note: "Note",
  readiness: "Design Readiness Gate",
  evaluate: "Evaluate readiness",
  notEvaluated: "Not evaluated yet.",
  select: "Select this concept",
  selectExplainer: "Selecting does not rank or reject other concepts.",
  reason: "Reason",
  acknowledge: "I acknowledge the reservations that need a human decision",
  reject: "Reject",
  ground: "Ground",
  reusableMechanisms: "Mechanisms worth reusing",
  rejectedBecause: "Rejected",
  saving: "Saving…",
};

export const designFr: DesignStrings = {
  tab: "Conception",
  requirements: "Exigences de conception",
  requirementsExplainer:
    "Les exigences précèdent les solutions. Chacune est rattachée à son origine ; une révision conserve la version antérieure.",
  noRequirements: "Aucune exigence de conception. Aucun concept ne peut être retenu avant d'en avoir.",
  newRequirement: "Nouvelle exigence",
  statement: "Énoncé",
  priority: "Priorité",
  basis: "Dérivée de",
  traceNote: "Note de traçabilité",
  addRequirement: "Ajouter l'exigence",
  confirm: "Confirmer",
  withdraw: "Retirer",
  withdrawReason: "Motif du retrait",
  proposedByAI: "Proposée par l'IA — à confirmer",
  version: "Version",
  concepts: "Concepts de conception",
  conceptsExplainer:
    "Les concepts gardent leur origine. Le choix vous revient après la porte de préparation à la conception ; les concepts rejetés restent dans l'historique.",
  noConcepts: "Aucun concept de conception.",
  newConcept: "Nouveau concept",
  title: "Titre",
  description: "Description",
  origin: "Origine",
  originReference: "Référence d'origine",
  hypotheses: "Hypothèses sur lesquelles il repose",
  mechanisms: "Mécanismes",
  derivedFrom: "Dérivé des concepts",
  addConcept: "Ajouter le concept",
  coverage: "Couverture des exigences",
  stale: "évaluée sur une version antérieure",
  recordCoverage: "Enregistrer la couverture",
  note: "Note",
  readiness: "Porte de préparation à la conception",
  evaluate: "Évaluer la préparation",
  notEvaluated: "Pas encore évalué.",
  select: "Retenir ce concept",
  selectExplainer: "Retenir un concept ne classe ni ne rejette les autres.",
  reason: "Motif",
  acknowledge: "Je prends acte des réserves qui exigent une décision humaine",
  reject: "Rejeter",
  ground: "Motif du rejet",
  reusableMechanisms: "Mécanismes à réutiliser",
  rejectedBecause: "Rejeté",
  saving: "Enregistrement…",
};

export const designAr: DesignStrings = {
  tab: "التصميم",
  requirements: "متطلبات التصميم",
  requirementsExplainer: "المتطلبات تسبق الحلول. كل متطلب مربوط بما اشتُق منه، والمراجعة تحفظ النسخة السابقة.",
  noRequirements: "لا توجد متطلبات تصميم بعد. لا يمكن اختيار أي تصور قبل وجودها.",
  newRequirement: "متطلب جديد",
  statement: "النص",
  priority: "الأولوية",
  basis: "مشتق من",
  traceNote: "ملاحظة الربط",
  addRequirement: "إضافة المتطلب",
  confirm: "تأكيد",
  withdraw: "سحب",
  withdrawReason: "سبب السحب",
  proposedByAI: "اقترحه الذكاء الاصطناعي — يحتاج إلى تأكيد",
  version: "النسخة",
  concepts: "تصورات التصميم",
  conceptsExplainer: "تحتفظ التصورات بمصدرها. الاختيار قرارك بعد بوابة جاهزية التصميم، والتصورات المرفوضة تبقى في السجل.",
  noConcepts: "لا توجد تصورات تصميم بعد.",
  newConcept: "تصور جديد",
  title: "العنوان",
  description: "الوصف",
  origin: "المصدر",
  originReference: "مرجع المصدر",
  hypotheses: "الفرضيات التي يبنى عليها",
  mechanisms: "الآليات",
  derivedFrom: "مشتق من تصورات",
  addConcept: "إضافة التصور",
  coverage: "تغطية المتطلبات",
  stale: "قُيّمت على نسخة سابقة",
  recordCoverage: "تسجيل التغطية",
  note: "ملاحظة",
  readiness: "بوابة جاهزية التصميم",
  evaluate: "تقييم الجاهزية",
  notEvaluated: "لم يُقيَّم بعد.",
  select: "اختيار هذا التصور",
  selectExplainer: "الاختيار لا يرتب التصورات الأخرى ولا يرفضها.",
  reason: "السبب",
  acknowledge: "أقرّ بالتحفظات التي تحتاج إلى قرار بشري",
  reject: "رفض",
  ground: "سبب الرفض",
  reusableMechanisms: "آليات تستحق إعادة الاستخدام",
  rejectedBecause: "مرفوض",
  saving: "جارٍ الحفظ…",
};
