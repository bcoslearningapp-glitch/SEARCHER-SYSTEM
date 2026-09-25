/** Research Core Package strings (en/fr/ar). */

export type PortabilityStrings = {
  export: string;
  importTitle: string;
  importExplainer: string;
  file: string;
  import: string;
  importing: string;
  imported: string;
  assetsRestored: string;
  metadataOnly: string;
  open: string;
};

export const portabilityEn: PortabilityStrings = {
  export: "Export package",
  importTitle: "Import a Research Core Package",
  importExplainer:
    "Checksums and the schema are verified before anything is written. Import never raises trust: foundational texts arrive staged, and sources whose files were withheld are metadata-only here.",
  file: "Package file (.zip)",
  import: "Import",
  importing: "Importing…",
  imported: "Imported",
  assetsRestored: "Files restored",
  metadataOnly: "Metadata-only sources",
  open: "Open project",
};

export const portabilityFr: PortabilityStrings = {
  export: "Exporter le paquet",
  importTitle: "Importer un paquet Research Core",
  importExplainer:
    "Les sommes de contrôle et le schéma sont vérifiés avant toute écriture. L'import n'augmente jamais la confiance : les textes fondateurs arrivent en attente d'approbation et les sources dont les fichiers ont été retenus n'ont ici que leurs métadonnées.",
  file: "Fichier du paquet (.zip)",
  import: "Importer",
  importing: "Import…",
  imported: "Importé",
  assetsRestored: "Fichiers restaurés",
  metadataOnly: "Sources en métadonnées seules",
  open: "Ouvrir le projet",
};

export const portabilityAr: PortabilityStrings = {
  export: "تصدير الحزمة",
  importTitle: "استيراد حزمة Research Core",
  importExplainer:
    "يُتحقق من المجاميع الاختبارية والمخطط قبل كتابة أي شيء. الاستيراد لا يرفع مستوى الثقة أبدًا: النصوص التأسيسية تصل بانتظار الاعتماد، والمصادر التي حُجبت ملفاتها تبقى هنا بياناتٍ وصفية فقط.",
  file: "ملف الحزمة (.zip)",
  import: "استيراد",
  importing: "جارٍ الاستيراد…",
  imported: "تم الاستيراد",
  assetsRestored: "ملفات مستعادة",
  metadataOnly: "مصادر ببيانات وصفية فقط",
  open: "فتح المشروع",
};
