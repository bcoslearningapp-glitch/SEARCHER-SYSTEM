/** Output strings (en/fr/ar). Canonical enum codes are displayed as-is. */

export type OutputStrings = {
  tab: string;
  explainer: string;
  outputs: string;
  noOutputs: string;
  newOutput: string;
  type: string;
  title: string;
  language: string;
  mode: string;
  subject: string;
  create: string;
  saving: string;
  version: string;
  versions: string;
  recompose: string;
  approve: string;
  approveExplainer: string;
  reason: string;
  setMode: string;
  protectedQuote: string;
  trace: string;
  references: string;
  projects: string;
  integrity: string;
  integrityExplainer: string;
  runIntegrity: string;
  notChecked: string;
  acknowledgeWarnings: string;
  export: string;
};

export const outputsEn: OutputStrings = {
  tab: "Outputs",
  explainer:
    "Outputs are composed from the project's recorded state. Every claim traces to its evidence, and exact quotes are copied from their sources and cannot be edited. Each change is a new version; only you approve one.",
  outputs: "Outputs",
  noOutputs: "No outputs yet.",
  newOutput: "New output",
  type: "Type",
  title: "Title",
  language: "Language",
  mode: "Mode",
  subject: "About",
  create: "Compose",
  saving: "Saving…",
  version: "Version",
  versions: "Versions",
  recompose: "Recompose from current state",
  approve: "Approve this version",
  approveExplainer: "Approval checks that quotes still match their sources and that every traced entity exists.",
  reason: "Reason",
  setMode: "Change mode",
  protectedQuote: "Exact quote (protected)",
  trace: "Traced to",
  references: "References",
  projects: "Projects",
  integrity: "Integrity pipeline",
  integrityExplainer:
    "Eight checks in order: claims, citations, exact quotes, reference integrity, terminology, translation strength, editing, rendering. A failed version cannot be approved; warnings need your decision.",
  runIntegrity: "Run integrity checks",
  notChecked: "Not checked yet.",
  acknowledgeWarnings: "I have reviewed the warnings",
  export: "Download",
};

export const outputsFr: OutputStrings = {
  tab: "Productions",
  explainer:
    "Les productions sont composées à partir de l'état enregistré du projet. Chaque affirmation renvoie à ses preuves, et les citations exactes sont copiées de leurs sources et ne peuvent pas être modifiées. Chaque changement crée une version ; vous seul en approuvez une.",
  outputs: "Productions",
  noOutputs: "Aucune production.",
  newOutput: "Nouvelle production",
  type: "Type",
  title: "Titre",
  language: "Langue",
  mode: "Mode",
  subject: "Sujet",
  create: "Composer",
  saving: "Enregistrement…",
  version: "Version",
  versions: "Versions",
  recompose: "Recomposer depuis l'état actuel",
  approve: "Approuver cette version",
  approveExplainer: "L'approbation vérifie que les citations correspondent toujours à leurs sources et que chaque entité citée existe.",
  reason: "Motif",
  setMode: "Changer de mode",
  protectedQuote: "Citation exacte (protégée)",
  trace: "Rattaché à",
  references: "Références",
  projects: "Projets",
  integrity: "Chaîne d'intégrité",
  integrityExplainer:
    "Huit contrôles dans l'ordre : affirmations, citations, citations exactes, intégrité de référence, terminologie, force de traduction, édition, rendu. Une version en échec ne peut pas être approuvée ; les avertissements demandent votre décision.",
  runIntegrity: "Lancer les contrôles d'intégrité",
  notChecked: "Pas encore contrôlé.",
  acknowledgeWarnings: "J'ai examiné les avertissements",
  export: "Télécharger",
};

export const outputsAr: OutputStrings = {
  tab: "المخرجات",
  explainer:
    "تُركَّب المخرجات من حالة المشروع المسجلة. كل ادعاء مربوط بأدلته، والاقتباسات الحرفية منسوخة من مصادرها ولا يمكن تعديلها. كل تغيير نسخة جديدة، وأنت وحدك من يعتمد نسخة.",
  outputs: "المخرجات",
  noOutputs: "لا توجد مخرجات بعد.",
  newOutput: "مخرج جديد",
  type: "النوع",
  title: "العنوان",
  language: "اللغة",
  mode: "النمط",
  subject: "الموضوع",
  create: "تركيب",
  saving: "جارٍ الحفظ…",
  version: "النسخة",
  versions: "النسخ",
  recompose: "إعادة التركيب من الحالة الحالية",
  approve: "اعتماد هذه النسخة",
  approveExplainer: "يتحقق الاعتماد من أن الاقتباسات ما زالت مطابقة لمصادرها وأن كل كيان مرتبط موجود.",
  reason: "السبب",
  setMode: "تغيير النمط",
  protectedQuote: "اقتباس حرفي (محمي)",
  trace: "مرتبط بـ",
  references: "المراجع",
  projects: "المشاريع",
  integrity: "سلسلة فحص السلامة",
  integrityExplainer:
    "ثمانية فحوص بالترتيب: الادعاءات، الإحالات، الاقتباسات الحرفية، السلامة المرجعية، المصطلحات، قوة الترجمة، التحرير، الإخراج. النسخة الفاشلة لا يمكن اعتمادها، والتنبيهات تحتاج إلى قرارك.",
  runIntegrity: "تشغيل فحوص السلامة",
  notChecked: "لم تُفحص بعد.",
  acknowledgeWarnings: "راجعتُ التنبيهات",
  export: "تنزيل",
};
