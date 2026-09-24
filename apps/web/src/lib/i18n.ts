/**
 * UI localization for the three first-class languages (PRD §3.1, NFR-I18N-001).
 * Arabic renders right-to-left; English and French left-to-right.
 * Canonical stored data is never localized; only presentation is.
 */

import { aiAr, aiEn, aiFr, type AIStrings } from "@/lib/i18n-ai";
import { designAr, designEn, designFr, type DesignStrings } from "@/lib/i18n-design";
import { experimentsAr, experimentsEn, experimentsFr, type ExperimentStrings } from "@/lib/i18n-experiments";
import { knowledgeAr, knowledgeEn, knowledgeFr, type KnowledgeStrings } from "@/lib/i18n-knowledge";
import { terminologyAr, terminologyEn, terminologyFr, type TerminologyStrings } from "@/lib/i18n-terminology";
import { closureAr, closureEn, closureFr, type ClosureStrings } from "@/lib/i18n-closure";
import { foundationalAr, foundationalEn, foundationalFr, type FoundationalStrings } from "@/lib/i18n-foundational";
import { labAr, labEn, labFr, type LabStrings } from "@/lib/i18n-lab";
import { reliabilityAr, reliabilityEn, reliabilityFr, type ReliabilityStrings } from "@/lib/i18n-reliability";
import { researchAr, researchEn, researchFr, type ResearchStrings } from "@/lib/i18n-research";
import { ar as uiAr, en as uiEn, fr as uiFr, type UiStrings } from "@/lib/i18n-ui";

export const LOCALES = ["en", "fr", "ar"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

export function dirFor(locale: Locale): "ltr" | "rtl" {
  return locale === "ar" ? "rtl" : "ltr";
}

export const SPACES = ["desk", "map", "library", "lab", "outputs"] as const;
export type Space = (typeof SPACES)[number];

export type Dictionary = {
  productName: string;
  ui: UiStrings;
  lab: LabStrings;
  ai: AIStrings;
  research: ResearchStrings;
  design: DesignStrings;
  experiments: ExperimentStrings;
  knowledge: KnowledgeStrings;
  terminology: TerminologyStrings;
  closure: ClosureStrings;
  foundational: FoundationalStrings;
  reliability: ReliabilityStrings;
  spaces: Record<Space, string>;
  spaceDescriptions: Record<Space, string>;
  notYetAvailable: string;
  systemStatus: string;
  status: { ready: string; degraded: string; unavailable: string; unreachable: string };
  components: { database: string; queue: string; aiProviders: string; none: string };
  languageName: string;
};

const en: Dictionary = {
  productName: "Integrated AI Research System",
  ui: uiEn,
  lab: labEn,
  ai: aiEn,
  research: researchEn,
  design: designEn,
  experiments: experimentsEn,
  knowledge: knowledgeEn,
  terminology: terminologyEn,
  closure: closureEn,
  foundational: foundationalEn,
  reliability: reliabilityEn,
  spaces: { desk: "Desk", map: "Map", library: "Library", lab: "Lab", outputs: "Outputs" },
  spaceDescriptions: {
    desk: "Current question, mode, next step, and items that need your attention.",
    map: "Central problem, hypotheses, open questions, decisions, and blockers.",
    library: "Foundational, digital, physical, restricted, and metadata-only sources.",
    lab: "Ideas, hypotheses, mechanisms, designs, experiments, and learning reviews.",
    outputs: "Reports, decision briefs, evidence maps, and exports with integrity status.",
  },
  notYetAvailable: "This space is not available yet.",
  systemStatus: "System status",
  status: { ready: "Ready", degraded: "Degraded", unavailable: "Unavailable", unreachable: "API unreachable" },
  components: { database: "Database", queue: "Background queue", aiProviders: "AI providers", none: "none configured" },
  languageName: "English",
};

const fr: Dictionary = {
  productName: "Système de recherche intégré à l'IA",
  ui: uiFr,
  lab: labFr,
  ai: aiFr,
  research: researchFr,
  design: designFr,
  experiments: experimentsFr,
  knowledge: knowledgeFr,
  terminology: terminologyFr,
  closure: closureFr,
  foundational: foundationalFr,
  reliability: reliabilityFr,
  spaces: { desk: "Bureau", map: "Carte", library: "Bibliothèque", lab: "Laboratoire", outputs: "Productions" },
  spaceDescriptions: {
    desk: "Question actuelle, mode, prochaine étape et éléments nécessitant votre attention.",
    map: "Problème central, hypothèses, questions ouvertes, décisions et blocages.",
    library: "Sources fondatrices, numériques, physiques, restreintes et métadonnées seules.",
    lab: "Idées, hypothèses, mécanismes, conceptions, expériences et bilans d'apprentissage.",
    outputs: "Rapports, notes de décision, cartes de preuves et exports avec statut d'intégrité.",
  },
  notYetAvailable: "Cet espace n'est pas encore disponible.",
  systemStatus: "État du système",
  status: { ready: "Prêt", degraded: "Dégradé", unavailable: "Indisponible", unreachable: "API injoignable" },
  components: {
    database: "Base de données",
    queue: "File de tâches",
    aiProviders: "Fournisseurs d'IA",
    none: "aucun configuré",
  },
  languageName: "Français",
};

const ar: Dictionary = {
  productName: "نظام البحث المتكامل بالذكاء الاصطناعي",
  ui: uiAr,
  lab: labAr,
  ai: aiAr,
  research: researchAr,
  design: designAr,
  experiments: experimentsAr,
  knowledge: knowledgeAr,
  terminology: terminologyAr,
  closure: closureAr,
  foundational: foundationalAr,
  reliability: reliabilityAr,
  spaces: { desk: "المكتب", map: "الخريطة", library: "المكتبة", lab: "المختبر", outputs: "المخرجات" },
  spaceDescriptions: {
    desk: "السؤال الحالي، والنمط، والخطوة التالية، والعناصر التي تحتاج إلى انتباهك.",
    map: "المشكلة المركزية، والفرضيات، والأسئلة المفتوحة، والقرارات، والعوائق.",
    library: "المصادر التأسيسية والرقمية والورقية والمقيدة والمصادر ذات البيانات الوصفية فقط.",
    lab: "الأفكار، والفرضيات، والآليات، والتصاميم، والتجارب، ومراجعات التعلم.",
    outputs: "التقارير، وموجزات القرار، وخرائط الأدلة، والتصدير مع حالة السلامة.",
  },
  notYetAvailable: "هذه المساحة غير متاحة بعد.",
  systemStatus: "حالة النظام",
  status: { ready: "جاهز", degraded: "متدهور", unavailable: "غير متاح", unreachable: "تعذر الوصول إلى الواجهة البرمجية" },
  components: { database: "قاعدة البيانات", queue: "طابور المهام", aiProviders: "مزودو الذكاء الاصطناعي", none: "لا يوجد" },
  languageName: "العربية",
};

const DICTIONARIES: Record<Locale, Dictionary> = { en, fr, ar };

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale];
}
