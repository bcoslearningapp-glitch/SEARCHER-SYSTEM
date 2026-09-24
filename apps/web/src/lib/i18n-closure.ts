/** Project closure and reopening strings (en/fr/ar). */

export type ClosureStrings = {
  title: string;
  explainer: string;
  closureType: string;
  resolved: string;
  unresolved: string;
  confidenceScope: string;
  limitations: string;
  openQuestions: string;
  reopenTriggers: string;
  listHint: string;
  acknowledge: string;
  overrideReason: string;
  close: string;
  closing: string;
  reopen: string;
  reopenTrigger: string;
  reopenExplainer: string;
  history: string;
  reopenedBecause: string;
};

export const closureEn: ClosureStrings = {
  title: "Closure",
  explainer:
    "Only you close a project. The Project Closure Gate checks open decisions, unfinished experiments, unassessed evidence and the closure record.",
  closureType: "Closure type",
  resolved: "Resolved",
  unresolved: "Unresolved",
  confidenceScope: "Confidence and scope",
  limitations: "Limitations",
  openQuestions: "Open questions",
  reopenTriggers: "What would reopen this project",
  listHint: "One per line",
  acknowledge: "I acknowledge the reservations that need a human decision",
  overrideReason: "Reason for closing despite them",
  close: "Close project",
  closing: "Closing…",
  reopen: "Reopen project",
  reopenTrigger: "Reopen trigger",
  reopenExplainer: "Earlier closure records are kept, and the Research State notes the trigger.",
  history: "Closure history",
  reopenedBecause: "Reopened because",
};

export const closureFr: ClosureStrings = {
  title: "Clôture",
  explainer:
    "Vous seul clôturez un projet. La porte de clôture vérifie les décisions ouvertes, les expériences inachevées, les preuves non évaluées et le dossier de clôture.",
  closureType: "Type de clôture",
  resolved: "Résolu",
  unresolved: "Non résolu",
  confidenceScope: "Confiance et portée",
  limitations: "Limites",
  openQuestions: "Questions ouvertes",
  reopenTriggers: "Ce qui rouvrirait ce projet",
  listHint: "Un par ligne",
  acknowledge: "Je prends acte des réserves qui exigent une décision humaine",
  overrideReason: "Motif de clôture malgré elles",
  close: "Clôturer le projet",
  closing: "Clôture…",
  reopen: "Rouvrir le projet",
  reopenTrigger: "Motif de réouverture",
  reopenExplainer: "Les dossiers de clôture antérieurs sont conservés et l'état de recherche note le motif.",
  history: "Historique des clôtures",
  reopenedBecause: "Rouvert parce que",
};

export const closureAr: ClosureStrings = {
  title: "الإغلاق",
  explainer:
    "أنت وحدك من يغلق المشروع. تتحقق بوابة إغلاق المشروع من القرارات المفتوحة والتجارب غير المكتملة والأدلة غير المقيّمة وسجل الإغلاق.",
  closureType: "نوع الإغلاق",
  resolved: "ما تم حسمه",
  unresolved: "ما لم يُحسم",
  confidenceScope: "الثقة والنطاق",
  limitations: "الحدود",
  openQuestions: "أسئلة مفتوحة",
  reopenTriggers: "ما الذي يعيد فتح هذا المشروع",
  listHint: "عنصر في كل سطر",
  acknowledge: "أقرّ بالتحفظات التي تحتاج إلى قرار بشري",
  overrideReason: "سبب الإغلاق رغمها",
  close: "إغلاق المشروع",
  closing: "جارٍ الإغلاق…",
  reopen: "إعادة فتح المشروع",
  reopenTrigger: "سبب إعادة الفتح",
  reopenExplainer: "تُحفظ سجلات الإغلاق السابقة، وتسجّل حالة البحث سبب إعادة الفتح.",
  history: "سجل الإغلاق",
  reopenedBecause: "أعيد فتحه بسبب",
};
