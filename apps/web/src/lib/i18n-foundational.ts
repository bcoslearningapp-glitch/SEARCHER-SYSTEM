/** Foundational library strings (en/fr/ar). Statuses are canonical codes shown as-is. */

export type FoundationalStrings = {
  title: string;
  link: string;
  explainer: string;
  sources: string;
  none: string;
  version: string;
  fingerprint: string;
  contents: string;
  approvedBy: string;
  importTitle: string;
  importExplainer: string;
  workTitle: string;
  editionVersion: string;
  editionHint: string;
  publisher: string;
  file: string;
  importing: string;
  import: string;
  imported: string;
  approveTitle: string;
  approveExplainer: string;
  reason: string;
  approve: string;
  approving: string;
  lookup: string;
  surah: string;
  ayah: string;
  to: string;
  show: string;
  noApproved: string;
  servedFrom: string;
};

export const foundationalEn: FoundationalStrings = {
  title: "Foundational library",
  link: "Foundational library (Qur'an text)",
  explainer:
    "The approved Qur'an text is imported from a published dataset and approved by the Constitutional Authority. The system never writes Qur'anic text itself, and nothing is served until approved.",
  sources: "Foundational sources",
  none: "No foundational source yet.",
  version: "Edition / version",
  fingerprint: "SHA-256 of the imported file",
  contents: "Contents",
  approvedBy: "Approved by",
  importTitle: "Import a Qur'an text dataset",
  importExplainer:
    "Accepted: KFGQPC developer JSON (e.g. warshData_v10.json) or the surah|ayah|text line format. The file is stored exactly as published and fingerprinted.",
  workTitle: "Title",
  editionVersion: "Edition and version",
  editionHint: "e.g. KFGQPC Uthmanic Warsh v10 (2021-08-05)",
  publisher: "Publisher",
  file: "Dataset file",
  importing: "Importing…",
  import: "Import (staged, not yet served)",
  imported: "Imported and staged. Review it, then approve.",
  approveTitle: "Approve as the served Qur'an text",
  approveExplainer:
    "Approval is a constitutional decision. It makes this text the one quoted everywhere in the product and retires any previously approved text.",
  reason: "Reason for approval",
  approve: "Approve",
  approving: "Approving…",
  lookup: "Look up ayat",
  surah: "Surah",
  ayah: "Ayah",
  to: "To ayah (optional)",
  show: "Show",
  noApproved: "No approved Qur'an text yet, so nothing can be quoted.",
  servedFrom: "Served from",
};

export const foundationalFr: FoundationalStrings = {
  title: "Bibliothèque fondamentale",
  link: "Bibliothèque fondamentale (texte du Coran)",
  explainer:
    "Le texte coranique approuvé est importé d'un jeu de données publié et approuvé par l'Autorité constitutionnelle. Le système n'écrit jamais lui-même de texte coranique, et rien n'est servi avant approbation.",
  sources: "Sources fondamentales",
  none: "Aucune source fondamentale.",
  version: "Édition / version",
  fingerprint: "SHA-256 du fichier importé",
  contents: "Contenu",
  approvedBy: "Approuvé par",
  importTitle: "Importer un jeu de données du texte coranique",
  importExplainer:
    "Formats acceptés : JSON développeur du KFGQPC (ex. warshData_v10.json) ou le format de lignes sourate|verset|texte. Le fichier est conservé tel que publié et identifié par son empreinte.",
  workTitle: "Titre",
  editionVersion: "Édition et version",
  editionHint: "ex. KFGQPC Uthmani Warsh v10 (2021-08-05)",
  publisher: "Éditeur",
  file: "Fichier du jeu de données",
  importing: "Importation…",
  import: "Importer (en attente, pas encore servi)",
  imported: "Importé et en attente. Vérifiez-le, puis approuvez-le.",
  approveTitle: "Approuver comme texte coranique servi",
  approveExplainer:
    "L'approbation est une décision constitutionnelle. Elle fait de ce texte celui cité partout dans le produit et retire tout texte approuvé précédemment.",
  reason: "Motif de l'approbation",
  approve: "Approuver",
  approving: "Approbation…",
  lookup: "Consulter des versets",
  surah: "Sourate",
  ayah: "Verset",
  to: "Jusqu'au verset (facultatif)",
  show: "Afficher",
  noApproved: "Aucun texte coranique approuvé : rien ne peut être cité.",
  servedFrom: "Servi depuis",
};

export const foundationalAr: FoundationalStrings = {
  title: "المكتبة التأسيسية",
  link: "المكتبة التأسيسية (نص القرآن)",
  explainer:
    "يُستورد نص القرآن المعتمد من مجموعة بيانات منشورة ويعتمده المرجع الدستوري. لا يكتب النظام نصاً قرآنياً من عنده أبداً، ولا يُعرض شيء قبل الاعتماد.",
  sources: "المصادر التأسيسية",
  none: "لا توجد مصادر تأسيسية بعد.",
  version: "الطبعة / الإصدار",
  fingerprint: "بصمة SHA-256 للملف المستورد",
  contents: "المحتوى",
  approvedBy: "اعتمده",
  importTitle: "استيراد مجموعة بيانات نص القرآن",
  importExplainer:
    "الصيغ المقبولة: ملف JSON للمطورين من مجمع الملك فهد (مثل warshData_v10.json) أو صيغة الأسطر سورة|آية|نص. يُحفظ الملف كما نُشر تماماً مع بصمته.",
  workTitle: "العنوان",
  editionVersion: "الطبعة والإصدار",
  editionHint: "مثال: مجمع الملك فهد – ورش العثماني الإصدار 10 (2021-08-05)",
  publisher: "الناشر",
  file: "ملف البيانات",
  importing: "جارٍ الاستيراد…",
  import: "استيراد (مرحلي، لا يُعرض بعد)",
  imported: "تم الاستيراد مرحلياً. راجعه ثم اعتمده.",
  approveTitle: "اعتماد النص ليكون نص القرآن المعروض",
  approveExplainer:
    "الاعتماد قرار دستوري. يجعل هذا النص هو المقتبس في كل مكان في المنتج، ويُحيل أي نص معتمد سابقاً إلى التقاعد.",
  reason: "سبب الاعتماد",
  approve: "اعتماد",
  approving: "جارٍ الاعتماد…",
  lookup: "عرض الآيات",
  surah: "السورة",
  ayah: "الآية",
  to: "إلى الآية (اختياري)",
  show: "عرض",
  noApproved: "لا يوجد نص قرآني معتمد بعد، لذا لا يمكن الاقتباس.",
  servedFrom: "مصدره",
};
