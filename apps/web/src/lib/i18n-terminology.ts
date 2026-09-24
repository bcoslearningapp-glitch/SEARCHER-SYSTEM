/** Terminology and translation-integrity strings (en/fr/ar). */

export type TerminologyStrings = {
  link: string;
  title: string;
  explainer: string;
  terms: string;
  noTerms: string;
  propose: string;
  term: string;
  originalLanguage: string;
  domain: string;
  definition: string;
  alternatives: string;
  alternativesHint: string;
  retainOriginal: string;
  sourceAuthority: string;
  approve: string;
  reject: string;
  reason: string;
  saving: string;
  checkTitle: string;
  checkExplainer: string;
  sourceLanguage: string;
  sourceText: string;
  targetLanguage: string;
  translatedText: string;
  check: string;
  checking: string;
  noDrift: string;
  review: string;
  screenNote: string;
  source: string;
  translation: string;
};

export const terminologyEn: TerminologyStrings = {
  link: "Terminology and translation check",
  title: "Terminology",
  explainer:
    "Canonical terms with approved Arabic, French and English renderings. Anyone can propose a term; a methodology steward approves the canonical form. A revision keeps earlier versions.",
  terms: "Terms",
  noTerms: "No terms yet.",
  propose: "Propose term",
  term: "Term",
  originalLanguage: "Original language",
  domain: "Domain",
  definition: "Definition",
  alternatives: "Alternative translations",
  alternativesHint: "One per line as language:text, e.g. fr:objectifs de la charia",
  retainOriginal: "Keep the original term in outputs",
  sourceAuthority: "Source or authority",
  approve: "Approve",
  reject: "Reject",
  reason: "Reason",
  saving: "Saving…",
  checkTitle: "Translation integrity check",
  checkExplainer:
    "Flags a translation that makes a claim stronger or weaker (e.g. association becoming causation, a dropped hedge, a wider scope) and approved terms not rendered as approved.",
  sourceLanguage: "Source language",
  sourceText: "Source text",
  targetLanguage: "Translation language",
  translatedText: "Translation",
  check: "Check",
  checking: "Checking…",
  noDrift: "No drift found",
  review: "Needs review",
  screenNote: "This is a deterministic screen for your review; a clean result does not prove the translation is faithful.",
  source: "Source",
  translation: "Translation",
};

export const terminologyFr: TerminologyStrings = {
  link: "Terminologie et contrôle de traduction",
  title: "Terminologie",
  explainer:
    "Termes canoniques avec leurs traductions arabe, française et anglaise approuvées. Chacun peut proposer un terme ; un responsable méthodologique approuve la forme canonique. Une révision conserve les versions antérieures.",
  terms: "Termes",
  noTerms: "Aucun terme.",
  propose: "Proposer un terme",
  term: "Terme",
  originalLanguage: "Langue d'origine",
  domain: "Domaine",
  definition: "Définition",
  alternatives: "Traductions alternatives",
  alternativesHint: "Une par ligne sous la forme langue:texte, p. ex. fr:objectifs de la charia",
  retainOriginal: "Conserver le terme original dans les productions",
  sourceAuthority: "Source ou autorité",
  approve: "Approuver",
  reject: "Rejeter",
  reason: "Motif",
  saving: "Enregistrement…",
  checkTitle: "Contrôle d'intégrité de traduction",
  checkExplainer:
    "Signale une traduction qui renforce ou affaiblit une affirmation (p. ex. une association devenue causalité, une nuance supprimée, une portée élargie) et les termes approuvés mal rendus.",
  sourceLanguage: "Langue source",
  sourceText: "Texte source",
  targetLanguage: "Langue de traduction",
  translatedText: "Traduction",
  check: "Contrôler",
  checking: "Contrôle…",
  noDrift: "Aucune dérive détectée",
  review: "À examiner",
  screenNote: "Il s'agit d'un filtrage déterministe à examiner ; un résultat sans alerte ne prouve pas la fidélité de la traduction.",
  source: "Source",
  translation: "Traduction",
};

export const terminologyAr: TerminologyStrings = {
  link: "المصطلحات وفحص الترجمة",
  title: "المصطلحات",
  explainer:
    "مصطلحات معتمدة مع ترجماتها العربية والفرنسية والإنجليزية المعتمدة. يمكن لأي أحد اقتراح مصطلح، ويعتمد أمين المنهجية الصيغة المعتمدة. والمراجعة تحفظ النسخ السابقة.",
  terms: "المصطلحات",
  noTerms: "لا توجد مصطلحات بعد.",
  propose: "اقتراح مصطلح",
  term: "المصطلح",
  originalLanguage: "اللغة الأصلية",
  domain: "المجال",
  definition: "التعريف",
  alternatives: "ترجمات بديلة",
  alternativesHint: "سطر لكل ترجمة بصيغة اللغة:النص، مثل fr:objectifs de la charia",
  retainOriginal: "الإبقاء على المصطلح الأصلي في المخرجات",
  sourceAuthority: "المصدر أو المرجعية",
  approve: "اعتماد",
  reject: "رفض",
  reason: "السبب",
  saving: "جارٍ الحفظ…",
  checkTitle: "فحص سلامة الترجمة",
  checkExplainer:
    "ينبّه إلى ترجمة تقوّي الادعاء أو تضعفه (كتحوّل الارتباط إلى سببية، أو حذف التحفّظ، أو توسيع النطاق) وإلى مصطلحات معتمدة لم تُترجم بالصيغة المعتمدة.",
  sourceLanguage: "لغة المصدر",
  sourceText: "النص المصدر",
  targetLanguage: "لغة الترجمة",
  translatedText: "الترجمة",
  check: "فحص",
  checking: "جارٍ الفحص…",
  noDrift: "لم يُعثر على انحراف",
  review: "يحتاج إلى مراجعة",
  screenNote: "هذا فحص آلي حتمي لمراجعتك؛ والنتيجة الخالية من التنبيهات لا تثبت أمانة الترجمة.",
  source: "المصدر",
  translation: "الترجمة",
};
