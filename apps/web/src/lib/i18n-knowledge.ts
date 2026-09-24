/** Local knowledge strings (en/fr/ar). Canonical enum codes are displayed as-is. */

export type KnowledgeStrings = {
  tab: string;
  explainer: string;
  items: string;
  noItems: string;
  newItem: string;
  statement: string;
  scope: string;
  contexts: string;
  listHint: string;
  basis: string;
  basisHint: string;
  contrarySearched: string;
  confidence: string;
  temporalProfile: string;
  interval: string;
  create: string;
  saving: string;
  revalidationDue: string;
  lastVerified: string;
  promote: string;
  promoteTo: string;
  promoteExplainer: string;
  reason: string;
  acknowledge: string;
  standing: string;
  action: string;
  targetStage: string;
  apply: string;
  reuse: string;
  reuseExplainer: string;
  targetProject: string;
  transferability: string;
  rationale: string;
  differences: string;
  reusedHere: string;
  noReused: string;
  notEvidence: string;
  fromProject: string;
};

export const knowledgeEn: KnowledgeStrings = {
  tab: "Knowledge",
  explainer:
    "Local knowledge moves from project finding to operating rule one stage at a time, and only when you promote it. It stays separate from foundational reference knowledge.",
  items: "Knowledge from this project",
  noItems: "No knowledge recorded yet. Close an experiment with a learning review first.",
  newItem: "Record knowledge",
  statement: "Statement",
  scope: "Scope",
  contexts: "Contexts",
  listHint: "One per line",
  basis: "Evidence basis",
  basisHint: "Interpretations and learning reviews from this project's experiments.",
  contrarySearched: "Contrary evidence has been searched",
  confidence: "Confidence",
  temporalProfile: "Time sensitivity",
  interval: "Revalidate every (days)",
  create: "Record",
  saving: "Saving…",
  revalidationDue: "Revalidation due",
  lastVerified: "Last verified",
  promote: "Promote",
  promoteTo: "Promote to",
  promoteExplainer: "The Knowledge Promotion Gate checks repetition, contrary evidence, scope and time validity.",
  reason: "Reason",
  acknowledge: "I acknowledge the reservations that need a human decision",
  standing: "Standing",
  action: "Action",
  targetStage: "Downgrade to",
  apply: "Apply",
  reuse: "Reuse in another project",
  reuseExplainer: "Similarity is not transferability. Your judgment is recorded as a label, and reused knowledge is never evidence there.",
  targetProject: "Project",
  transferability: "Transferability",
  rationale: "Rationale",
  differences: "Differences",
  reusedHere: "Knowledge reused in this project",
  noReused: "None. Nothing is reused automatically.",
  notEvidence: "Not evidence in this project",
  fromProject: "From project",
};

export const knowledgeFr: KnowledgeStrings = {
  tab: "Connaissances",
  explainer:
    "Les connaissances locales passent du constat de projet à la règle opératoire une étape à la fois, et seulement quand vous les promouvez. Elles restent distinctes des connaissances de référence fondatrices.",
  items: "Connaissances de ce projet",
  noItems: "Aucune connaissance enregistrée. Clôturez d'abord une expérience par une revue d'apprentissage.",
  newItem: "Enregistrer une connaissance",
  statement: "Énoncé",
  scope: "Portée",
  contexts: "Contextes",
  listHint: "Un par ligne",
  basis: "Base de preuves",
  basisHint: "Interprétations et revues d'apprentissage des expériences de ce projet.",
  contrarySearched: "Les preuves contraires ont été recherchées",
  confidence: "Confiance",
  temporalProfile: "Sensibilité au temps",
  interval: "Revalider tous les (jours)",
  create: "Enregistrer",
  saving: "Enregistrement…",
  revalidationDue: "Revalidation due",
  lastVerified: "Dernière vérification",
  promote: "Promouvoir",
  promoteTo: "Promouvoir en",
  promoteExplainer: "La porte de promotion vérifie la répétition, les preuves contraires, la portée et la validité temporelle.",
  reason: "Motif",
  acknowledge: "Je prends acte des réserves qui exigent une décision humaine",
  standing: "Statut",
  action: "Action",
  targetStage: "Rétrograder en",
  apply: "Appliquer",
  reuse: "Réutiliser dans un autre projet",
  reuseExplainer:
    "La similarité n'est pas la transférabilité. Votre jugement est enregistré comme étiquette, et la connaissance réutilisée n'y est jamais une preuve.",
  targetProject: "Projet",
  transferability: "Transférabilité",
  rationale: "Justification",
  differences: "Différences",
  reusedHere: "Connaissances réutilisées dans ce projet",
  noReused: "Aucune. Rien n'est réutilisé automatiquement.",
  notEvidence: "Pas une preuve dans ce projet",
  fromProject: "Projet d'origine",
};

export const knowledgeAr: KnowledgeStrings = {
  tab: "المعرفة",
  explainer:
    "تنتقل المعرفة المحلية من نتيجة مشروع إلى قاعدة تشغيلية مرحلة بعد مرحلة، وفقط عندما ترقّيها أنت. وتبقى منفصلة عن المعرفة المرجعية التأسيسية.",
  items: "معرفة هذا المشروع",
  noItems: "لا توجد معرفة مسجلة بعد. أغلق تجربة بمراجعة تعلّم أولًا.",
  newItem: "تسجيل معرفة",
  statement: "النص",
  scope: "النطاق",
  contexts: "السياقات",
  listHint: "عنصر في كل سطر",
  basis: "أساس الأدلة",
  basisHint: "تفسيرات ومراجعات تعلّم من تجارب هذا المشروع.",
  contrarySearched: "تم البحث عن الأدلة المعارضة",
  confidence: "الثقة",
  temporalProfile: "الحساسية للزمن",
  interval: "إعادة التحقق كل (أيام)",
  create: "تسجيل",
  saving: "جارٍ الحفظ…",
  revalidationDue: "إعادة التحقق مستحقة",
  lastVerified: "آخر تحقق",
  promote: "ترقية",
  promoteTo: "ترقية إلى",
  promoteExplainer: "تتحقق بوابة ترقية المعرفة من التكرار والأدلة المعارضة والنطاق والصلاحية الزمنية.",
  reason: "السبب",
  acknowledge: "أقرّ بالتحفظات التي تحتاج إلى قرار بشري",
  standing: "الوضع",
  action: "الإجراء",
  targetStage: "خفض إلى",
  apply: "تطبيق",
  reuse: "إعادة الاستخدام في مشروع آخر",
  reuseExplainer: "التشابه ليس قابلية للنقل. يُسجَّل حكمك وسمًا، والمعرفة المعاد استخدامها ليست دليلًا هناك أبدًا.",
  targetProject: "المشروع",
  transferability: "قابلية النقل",
  rationale: "المسوّغ",
  differences: "الفروق",
  reusedHere: "معرفة أعيد استخدامها في هذا المشروع",
  noReused: "لا شيء. لا يُعاد استخدام شيء تلقائيًا.",
  notEvidence: "ليست دليلًا في هذا المشروع",
  fromProject: "من المشروع",
};
