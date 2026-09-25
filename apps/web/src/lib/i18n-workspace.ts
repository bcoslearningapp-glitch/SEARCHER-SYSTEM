/** Selective cloud workspace strings (en/fr/ar). */

export type WorkspaceStrings = {
  tab: string;
  explainer: string;
  notConfigured: string;
  adapter: string;
  stageTitle: string;
  purpose: string;
  ttl: string;
  select: string;
  nothingToSelect: string;
  stage: string;
  staging: string;
  manifest: string;
  noStagings: string;
  policy: string;
  expires: string;
  items: string;
  delete: string;
  deleting: string;
  deleteReason: string;
  kinds: Record<"SourceExcerpt" | "Claim" | "Hypothesis" | "OutputVersion", string>;
};

export const workspaceEn: WorkspaceStrings = {
  tab: "Workspace",
  explainer:
    "Stage selected records in a remote research workspace. Nothing is synchronised: only what you tick leaves, after the project's disclosure policy is checked. Every attempt, allowed or blocked, is kept in the disclosure manifest. The local database stays canonical.",
  notConfigured: "No cloud workspace is configured for this installation. Local retrieval mode keeps working as before.",
  adapter: "Workspace",
  stageTitle: "Stage a selection",
  purpose: "Purpose",
  ttl: "Keep for (hours)",
  select: "Records to stage",
  nothingToSelect: "This project has no claims, hypotheses, excerpts or outputs yet.",
  stage: "Stage",
  staging: "Staging…",
  manifest: "Disclosure manifest",
  noStagings: "Nothing has been staged.",
  policy: "Policy",
  expires: "Expires",
  items: "Items",
  delete: "Delete from workspace",
  deleting: "Deleting…",
  deleteReason: "Reason",
  kinds: { SourceExcerpt: "Excerpt", Claim: "Claim", Hypothesis: "Hypothesis", OutputVersion: "Output version" },
};

export const workspaceFr: WorkspaceStrings = {
  tab: "Espace distant",
  explainer:
    "Déposez des éléments choisis dans un espace de recherche distant. Rien n'est synchronisé : seul ce que vous cochez part, après vérification de la politique de divulgation du projet. Chaque tentative, autorisée ou bloquée, est conservée dans le registre de divulgation. La base locale reste la référence.",
  notConfigured: "Aucun espace distant n'est configuré pour cette installation. Le mode de recherche locale continue de fonctionner.",
  adapter: "Espace",
  stageTitle: "Déposer une sélection",
  purpose: "Objet",
  ttl: "Conserver (heures)",
  select: "Éléments à déposer",
  nothingToSelect: "Ce projet n'a encore ni affirmations, ni hypothèses, ni extraits, ni productions.",
  stage: "Déposer",
  staging: "Dépôt…",
  manifest: "Registre de divulgation",
  noStagings: "Rien n'a été déposé.",
  policy: "Politique",
  expires: "Expire",
  items: "Éléments",
  delete: "Supprimer de l'espace",
  deleting: "Suppression…",
  deleteReason: "Motif",
  kinds: { SourceExcerpt: "Extrait", Claim: "Affirmation", Hypothesis: "Hypothèse", OutputVersion: "Version de production" },
};

export const workspaceAr: WorkspaceStrings = {
  tab: "مساحة العمل",
  explainer:
    "ضع سجلات مختارة في مساحة بحث بعيدة. لا تجري أي مزامنة: لا يخرج إلا ما تحدده، بعد التحقق من سياسة الإفصاح للمشروع. تُحفظ كل محاولة، مسموحة كانت أم محجوبة، في سجل الإفصاح. تبقى قاعدة البيانات المحلية هي المرجع.",
  notConfigured: "لم تُضبط أي مساحة عمل سحابية لهذا التثبيت. يستمر وضع الاسترجاع المحلي في العمل كما هو.",
  adapter: "المساحة",
  stageTitle: "وضع مجموعة مختارة",
  purpose: "الغرض",
  ttl: "مدة الحفظ (ساعات)",
  select: "السجلات المراد وضعها",
  nothingToSelect: "لا يحتوي هذا المشروع بعد على ادعاءات أو فرضيات أو مقتطفات أو مخرجات.",
  stage: "وضع",
  staging: "جارٍ الوضع…",
  manifest: "سجل الإفصاح",
  noStagings: "لم يوضع شيء بعد.",
  policy: "السياسة",
  expires: "ينتهي",
  items: "العناصر",
  delete: "حذف من المساحة",
  deleting: "جارٍ الحذف…",
  deleteReason: "السبب",
  kinds: { SourceExcerpt: "مقتطف", Claim: "ادعاء", Hypothesis: "فرضية", OutputVersion: "نسخة مخرج" },
};
