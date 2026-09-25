/** AI assistance strings (en/fr/ar). Job states and failure kinds are canonical codes shown as-is. */

export type AIStrings = {
  title: string;
  explainer: string;
  unavailable: string;
  draftFrame: string;
  detectAssumptions: string;
  challenge: string;
  challengeExplainer: string;
  launching: string;
  queued: string;
  tasks: string;
  noTasks: string;
  working: string;
  providerFailure: string;
  budgetStop: string;
  policy: string;
  policyExplainer: string;
  cloudConsent: string;
  allowedProfiles: string;
  anyProfile: string;
  preferredProfile: string;
  projectBudget: string;
  taskBudget: string;
  spent: string;
  savePolicy: string;
  saving: string;
  taskNames: Record<string, string>;
};

export const aiEn: AIStrings = {
  title: "AI assistance",
  explainer:
    "AI drafts and proposes; nothing it produces is accepted until you review it. Your project stays fully usable without AI.",
  unavailable: "No AI provider is configured. Everything else keeps working; add a key to enable AI assistance.",
  draftFrame: "Draft Problem Frame with AI",
  detectAssumptions: "Detect hidden assumptions",
  challenge: "Challenge this",
  challengeExplainer:
    "Searches your library for counter-evidence and alternative explanations. Findings arrive as candidates for you to assess.",
  launching: "Starting…",
  queued: "Task queued. Progress appears below.",
  tasks: "AI tasks",
  noTasks: "No AI tasks yet.",
  working: "Working…",
  providerFailure: "The AI provider failed. Nothing was changed, and the failure is recorded; it does not mean no evidence exists.",
  budgetStop: "Stopped: the AI budget for this project or task is exhausted.",
  policy: "Project AI policy",
  policyExplainer: "Controls what may reach cloud AI for this project. Confidential projects need consent; restricted and critical projects never send content to cloud AI.",
  cloudConsent: "Allow cloud AI for this confidential project (explicit consent)",
  allowedProfiles: "Allowed model profiles",
  anyProfile: "Leave all unticked to allow any configured profile.",
  preferredProfile: "Preferred profile",
  projectBudget: "Project budget (USD)",
  taskBudget: "Per-task budget (USD)",
  spent: "Spent so far",
  savePolicy: "Save policy",
  saving: "Saving…",
  taskNames: {
    "orchestrator.draft_problem_frame": "Draft Problem Frame",
    "orchestrator.detect_assumptions": "Detect assumptions",
    "orchestrator.challenge": "Challenge this",
  },
};

export const aiFr: AIStrings = {
  title: "Assistance IA",
  explainer:
    "L'IA rédige et propose ; rien n'est accepté avant votre examen. Votre projet reste pleinement utilisable sans IA.",
  unavailable:
    "Aucun fournisseur d'IA n'est configuré. Tout le reste fonctionne ; ajoutez une clé pour activer l'assistance IA.",
  draftFrame: "Rédiger le cadrage avec l'IA",
  detectAssumptions: "Détecter les hypothèses implicites",
  challenge: "Contester",
  challengeExplainer:
    "Recherche dans votre bibliothèque des contre-preuves et des explications alternatives. Les résultats arrivent comme candidats à évaluer.",
  launching: "Démarrage…",
  queued: "Tâche en file d'attente. La progression s'affiche ci-dessous.",
  tasks: "Tâches IA",
  noTasks: "Aucune tâche IA pour l'instant.",
  working: "En cours…",
  providerFailure:
    "Le fournisseur d'IA a échoué. Rien n'a été modifié et l'échec est enregistré ; cela ne signifie pas l'absence de preuves.",
  budgetStop: "Arrêté : le budget IA du projet ou de la tâche est épuisé.",
  policy: "Politique IA du projet",
  policyExplainer: "Détermine ce qui peut être envoyé à l'IA en nuage pour ce projet. Les projets confidentiels exigent un consentement ; les projets restreints et critiques n'envoient jamais de contenu à l'IA en nuage.",
  cloudConsent: "Autoriser l'IA en nuage pour ce projet confidentiel (consentement explicite)",
  allowedProfiles: "Profils de modèle autorisés",
  anyProfile: "Ne cochez rien pour autoriser tout profil configuré.",
  preferredProfile: "Profil préféré",
  projectBudget: "Budget du projet (USD)",
  taskBudget: "Budget par tâche (USD)",
  spent: "Dépensé à ce jour",
  savePolicy: "Enregistrer la politique",
  saving: "Enregistrement…",
  taskNames: {
    "orchestrator.draft_problem_frame": "Rédiger le cadrage",
    "orchestrator.detect_assumptions": "Détecter les hypothèses implicites",
    "orchestrator.challenge": "Contester",
  },
};

export const aiAr: AIStrings = {
  title: "المساعدة بالذكاء الاصطناعي",
  explainer: "يصوغ الذكاء الاصطناعي ويقترح فقط؛ ولا يُعتمد شيء قبل مراجعتك. يبقى مشروعك قابلاً للاستخدام بالكامل دون الذكاء الاصطناعي.",
  unavailable: "لم يُضبط أي مزوّد للذكاء الاصطناعي. كل ما عدا ذلك يعمل؛ أضف مفتاحاً لتفعيل المساعدة.",
  draftFrame: "صياغة إطار المشكلة بالذكاء الاصطناعي",
  detectAssumptions: "كشف الافتراضات الضمنية",
  challenge: "اعترض على هذا",
  challengeExplainer: "يبحث في مكتبتك عن أدلة مضادة وتفسيرات بديلة. تصل النتائج كمرشّحات لتقيّمها أنت.",
  launching: "جارٍ البدء…",
  queued: "أُضيفت المهمة إلى قائمة الانتظار. يظهر التقدّم أدناه.",
  tasks: "مهام الذكاء الاصطناعي",
  noTasks: "لا توجد مهام بعد.",
  working: "قيد العمل…",
  providerFailure: "تعذّر على مزوّد الذكاء الاصطناعي الإكمال. لم يتغيّر شيء، وسُجّل الإخفاق؛ وهذا لا يعني عدم وجود أدلة.",
  budgetStop: "توقّف: نفدت ميزانية الذكاء الاصطناعي للمشروع أو المهمة.",
  policy: "سياسة الذكاء الاصطناعي للمشروع",
  policyExplainer: "تحدد ما يجوز إرساله إلى الذكاء الاصطناعي السحابي في هذا المشروع. المشاريع السرية تتطلب موافقة صريحة؛ والمشاريع المقيّدة والحرجة لا ترسل أي محتوى إلى الذكاء الاصطناعي السحابي أبدًا.",
  cloudConsent: "السماح بالذكاء الاصطناعي السحابي لهذا المشروع السري (موافقة صريحة)",
  allowedProfiles: "ملفات النماذج المسموح بها",
  anyProfile: "اترك الكل دون تحديد للسماح بأي ملف مُهيّأ.",
  preferredProfile: "الملف المفضّل",
  projectBudget: "ميزانية المشروع (دولار)",
  taskBudget: "ميزانية كل مهمة (دولار)",
  spent: "المصروف حتى الآن",
  savePolicy: "حفظ السياسة",
  saving: "جارٍ الحفظ…",
  taskNames: {
    "orchestrator.draft_problem_frame": "صياغة إطار المشكلة",
    "orchestrator.detect_assumptions": "كشف الافتراضات",
    "orchestrator.challenge": "اعترض على هذا",
  },
};
