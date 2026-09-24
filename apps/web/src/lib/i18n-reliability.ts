/** AI reliability registry strings (en/fr/ar). Dimension keys and statuses are canonical codes. */

export type ReliabilityStrings = {
  title: string;
  link: string;
  explainer: string;
  operational: string;
  noCalls: string;
  provider: string;
  model: string;
  task: string;
  calls: string;
  succeeded: string;
  invalid: string;
  refusals: string;
  unavailable: string;
  blocked: string;
  reliability: string;
  cost: string;
  models: string;
  noEvaluations: string;
  dimension: string;
  threshold: string;
  score: string;
  passed: string;
  failed: string;
  notEvaluated: string;
  blockingGaps: string;
  thresholds: string;
  blocking: string;
};

export const reliabilityEn: ReliabilityStrings = {
  title: "AI reliability",
  link: "AI reliability registry",
  explainer:
    "What each model actually did here, and how it scored on the evaluation suite. A model is ready for default use only when every blocking dimension passes. Changing a model never rewrites existing knowledge.",
  operational: "Observed use (from the request log)",
  noCalls: "No AI calls recorded yet.",
  provider: "Provider",
  model: "Model",
  task: "Task",
  calls: "Calls",
  succeeded: "Succeeded",
  invalid: "Invalid output",
  refusals: "Refusals",
  unavailable: "Unavailable",
  blocked: "Blocked by policy",
  reliability: "Structured-output reliability",
  cost: "Estimated cost (USD)",
  models: "Evaluated models",
  noEvaluations: "No evaluation results recorded yet.",
  dimension: "Dimension",
  threshold: "Threshold",
  score: "Latest score",
  passed: "passes",
  failed: "fails",
  notEvaluated: "not evaluated",
  blockingGaps: "Blocking dimensions failing or not evaluated",
  thresholds: "Dimensions and thresholds",
  blocking: "blocking",
};

export const reliabilityFr: ReliabilityStrings = {
  title: "Fiabilité de l'IA",
  link: "Registre de fiabilité de l'IA",
  explainer:
    "Ce que chaque modèle a réellement fait ici et ses résultats sur la suite d'évaluation. Un modèle n'est prêt pour un usage par défaut que si toutes les dimensions bloquantes passent. Changer de modèle ne réécrit jamais les connaissances existantes.",
  operational: "Usage observé (journal des requêtes)",
  noCalls: "Aucun appel IA enregistré.",
  provider: "Fournisseur",
  model: "Modèle",
  task: "Tâche",
  calls: "Appels",
  succeeded: "Réussis",
  invalid: "Sortie invalide",
  refusals: "Refus",
  unavailable: "Indisponible",
  blocked: "Bloqués par la politique",
  reliability: "Fiabilité de la sortie structurée",
  cost: "Coût estimé (USD)",
  models: "Modèles évalués",
  noEvaluations: "Aucun résultat d'évaluation enregistré.",
  dimension: "Dimension",
  threshold: "Seuil",
  score: "Dernier score",
  passed: "réussit",
  failed: "échoue",
  notEvaluated: "non évalué",
  blockingGaps: "Dimensions bloquantes en échec ou non évaluées",
  thresholds: "Dimensions et seuils",
  blocking: "bloquante",
};

export const reliabilityAr: ReliabilityStrings = {
  title: "موثوقية الذكاء الاصطناعي",
  link: "سجل موثوقية الذكاء الاصطناعي",
  explainer:
    "ما فعله كل نموذج فعلياً هنا، ونتائجه في مجموعة التقييم. لا يصلح النموذج للاستخدام الافتراضي إلا إذا نجح في كل الأبعاد الحاجبة. وتغيير النموذج لا يعيد كتابة المعرفة القائمة أبداً.",
  operational: "الاستخدام الملاحظ (من سجل الطلبات)",
  noCalls: "لا توجد استدعاءات مسجلة بعد.",
  provider: "المزوّد",
  model: "النموذج",
  task: "المهمة",
  calls: "الاستدعاءات",
  succeeded: "الناجحة",
  invalid: "مخرجات غير صالحة",
  refusals: "الرفض",
  unavailable: "غير متاح",
  blocked: "محجوبة بالسياسة",
  reliability: "موثوقية المخرجات المهيكلة",
  cost: "التكلفة التقديرية (دولار)",
  models: "النماذج المقيَّمة",
  noEvaluations: "لا توجد نتائج تقييم مسجلة بعد.",
  dimension: "البُعد",
  threshold: "العتبة",
  score: "آخر نتيجة",
  passed: "ناجح",
  failed: "راسب",
  notEvaluated: "غير مقيَّم",
  blockingGaps: "أبعاد حاجبة راسبة أو غير مقيَّمة",
  thresholds: "الأبعاد والعتبات",
  blocking: "حاجب",
};
