/** Design hypothesis and experiment strings (en/fr/ar). Canonical enum codes are displayed as-is. */

type ContentField =
  | "intervention"
  | "target_population"
  | "context"
  | "mechanism"
  | "expected_outcome"
  | "measurement_plan"
  | "failure_conditions"
  | "side_effects"
  | "stop_conditions";
type ProtocolField = "method" | "sample" | "duration" | "data_collected" | "analysis_plan" | "success_criteria";

export type ExperimentStrings = {
  tab: string;
  designHypotheses: string;
  noDesignHypotheses: string;
  newDesignHypothesis: string;
  concept: string;
  content: Record<ContentField, string>;
  listHint: string;
  affectsPeople: string;
  affectsPeopleHint: string;
  create: string;
  saving: string;
  assess: string;
  assessHint: string;
  reason: string;
  experiments: string;
  noExperiments: string;
  newExperiment: string;
  designHypothesis: string;
  title: string;
  protocol: string;
  protocolFields: Record<ProtocolField, string>;
  saveProtocol: string;
  state: string;
  invalidated: string;
  moveTo: string;
  move: string;
  acknowledge: string;
  history: string;
  humanImpact: string;
  humanImpactExplainer: string;
  dimension: string;
  finding: string;
  note: string;
  externalAuthority: string;
  record: string;
  observations: string;
  observationExplainer: string;
  observedAt: string;
  description: string;
  results: string;
  resultExplainer: string;
  method: string;
  summary: string;
  fromObservations: string;
  interpretations: string;
  interpretationExplainer: string;
  outcome: string;
  statement: string;
  limitations: string;
  fromResults: string;
  none: string;
};

export const experimentsEn: ExperimentStrings = {
  tab: "Experiments",
  designHypotheses: "Design hypotheses",
  noDesignHypotheses: "No design hypotheses yet. Add a design concept first.",
  newDesignHypothesis: "New design hypothesis",
  concept: "Design concept",
  content: {
    intervention: "Intervention",
    target_population: "Target population",
    context: "Context",
    mechanism: "Mechanism",
    expected_outcome: "Expected outcome",
    measurement_plan: "Measurement plan",
    failure_conditions: "Failure conditions",
    side_effects: "Possible side effects",
    stop_conditions: "Stop conditions",
  },
  listHint: "One per line",
  affectsPeople: "People are affected",
  affectsPeopleHint: "Experiments that affect people need a human-impact review before approval.",
  create: "Create",
  saving: "Saving…",
  assess: "Assess",
  assessHint: "Based on interpretations of interpreted experiments. Invalidated experiments do not count.",
  reason: "Reason",
  experiments: "Experiments",
  noExperiments: "No experiments yet.",
  newExperiment: "New experiment",
  designHypothesis: "Design hypothesis",
  title: "Title",
  protocol: "Protocol",
  protocolFields: {
    method: "Method",
    sample: "Sample",
    duration: "Duration",
    data_collected: "Data collected",
    analysis_plan: "Analysis plan",
    success_criteria: "Success criteria",
  },
  saveProtocol: "Save protocol",
  state: "State",
  invalidated: "Invalidated: this is not a failed test of the hypothesis.",
  moveTo: "Move to",
  move: "Move",
  acknowledge: "I acknowledge the reservations that need a human decision",
  history: "History",
  humanImpact: "Human-impact review",
  humanImpactExplainer:
    "Privacy, consent, harm, authority, law and policy, data handling, institutional approval and reversibility. This is separate from the reference judgment; a required external approval becomes an open operational requirement.",
  dimension: "Dimension",
  finding: "Finding",
  note: "Note",
  externalAuthority: "Approving authority",
  record: "Record",
  observations: "Observations",
  observationExplainer: "What was observed, as it happened. Recorded only while the experiment is running.",
  observedAt: "Observed at",
  description: "Description",
  results: "Analysed results",
  resultExplainer: "Derived from named observations during analysis.",
  method: "Method",
  summary: "Summary",
  fromObservations: "From observations",
  interpretations: "Interpretations",
  interpretationExplainer: "Your reading of the analysed results for the design hypothesis.",
  outcome: "Outcome",
  statement: "Statement",
  limitations: "Limitations",
  fromResults: "From results",
  none: "None yet.",
};

export const experimentsFr: ExperimentStrings = {
  tab: "Expériences",
  designHypotheses: "Hypothèses de conception",
  noDesignHypotheses: "Aucune hypothèse de conception. Ajoutez d'abord un concept.",
  newDesignHypothesis: "Nouvelle hypothèse de conception",
  concept: "Concept de conception",
  content: {
    intervention: "Intervention",
    target_population: "Population cible",
    context: "Contexte",
    mechanism: "Mécanisme",
    expected_outcome: "Résultat attendu",
    measurement_plan: "Plan de mesure",
    failure_conditions: "Conditions d'échec",
    side_effects: "Effets secondaires possibles",
    stop_conditions: "Conditions d'arrêt",
  },
  listHint: "Une par ligne",
  affectsPeople: "Des personnes sont concernées",
  affectsPeopleHint: "Les expériences qui concernent des personnes exigent une revue d'impact humain avant approbation.",
  create: "Créer",
  saving: "Enregistrement…",
  assess: "Évaluer",
  assessHint: "Fondé sur les interprétations d'expériences interprétées. Les expériences invalidées ne comptent pas.",
  reason: "Motif",
  experiments: "Expériences",
  noExperiments: "Aucune expérience.",
  newExperiment: "Nouvelle expérience",
  designHypothesis: "Hypothèse de conception",
  title: "Titre",
  protocol: "Protocole",
  protocolFields: {
    method: "Méthode",
    sample: "Échantillon",
    duration: "Durée",
    data_collected: "Données collectées",
    analysis_plan: "Plan d'analyse",
    success_criteria: "Critères de succès",
  },
  saveProtocol: "Enregistrer le protocole",
  state: "État",
  invalidated: "Invalidée : ce n'est pas un test échoué de l'hypothèse.",
  moveTo: "Passer à",
  move: "Valider",
  acknowledge: "Je prends acte des réserves qui exigent une décision humaine",
  history: "Historique",
  humanImpact: "Revue d'impact humain",
  humanImpactExplainer:
    "Vie privée, consentement, préjudice, autorité, droit et règles, traitement des données, approbation institutionnelle et réversibilité. Distincte du jugement de référence ; une approbation externe requise devient une exigence opérationnelle ouverte.",
  dimension: "Dimension",
  finding: "Constat",
  note: "Note",
  externalAuthority: "Autorité d'approbation",
  record: "Enregistrer",
  observations: "Observations",
  observationExplainer: "Ce qui a été observé, au moment où cela s'est produit. Uniquement pendant l'exécution.",
  observedAt: "Observé le",
  description: "Description",
  results: "Résultats analysés",
  resultExplainer: "Dérivés d'observations nommées pendant l'analyse.",
  method: "Méthode",
  summary: "Synthèse",
  fromObservations: "À partir des observations",
  interpretations: "Interprétations",
  interpretationExplainer: "Votre lecture des résultats analysés pour l'hypothèse de conception.",
  outcome: "Conclusion",
  statement: "Énoncé",
  limitations: "Limites",
  fromResults: "À partir des résultats",
  none: "Rien pour l'instant.",
};

export const experimentsAr: ExperimentStrings = {
  tab: "التجارب",
  designHypotheses: "فرضيات التصميم",
  noDesignHypotheses: "لا توجد فرضيات تصميم بعد. أضف تصور تصميم أولًا.",
  newDesignHypothesis: "فرضية تصميم جديدة",
  concept: "تصور التصميم",
  content: {
    intervention: "التدخل",
    target_population: "الفئة المستهدفة",
    context: "السياق",
    mechanism: "الآلية",
    expected_outcome: "النتيجة المتوقعة",
    measurement_plan: "خطة القياس",
    failure_conditions: "شروط الإخفاق",
    side_effects: "الآثار الجانبية المحتملة",
    stop_conditions: "شروط الإيقاف",
  },
  listHint: "عنصر في كل سطر",
  affectsPeople: "تمس أشخاصًا",
  affectsPeopleHint: "التجارب التي تمس أشخاصًا تحتاج إلى مراجعة الأثر البشري قبل الموافقة.",
  create: "إنشاء",
  saving: "جارٍ الحفظ…",
  assess: "تقييم",
  assessHint: "يستند إلى تفسيرات تجارب مكتملة التفسير. التجارب الملغاة لا تُحتسب.",
  reason: "السبب",
  experiments: "التجارب",
  noExperiments: "لا توجد تجارب بعد.",
  newExperiment: "تجربة جديدة",
  designHypothesis: "فرضية التصميم",
  title: "العنوان",
  protocol: "البروتوكول",
  protocolFields: {
    method: "المنهج",
    sample: "العينة",
    duration: "المدة",
    data_collected: "البيانات المجمعة",
    analysis_plan: "خطة التحليل",
    success_criteria: "معايير النجاح",
  },
  saveProtocol: "حفظ البروتوكول",
  state: "الحالة",
  invalidated: "ملغاة: هذا ليس اختبارًا فاشلًا للفرضية.",
  moveTo: "نقل إلى",
  move: "نقل",
  acknowledge: "أقرّ بالتحفظات التي تحتاج إلى قرار بشري",
  history: "السجل",
  humanImpact: "مراجعة الأثر البشري",
  humanImpactExplainer:
    "الخصوصية والموافقة والضرر والصلاحية والقانون والسياسات ومعالجة البيانات والموافقة المؤسسية وقابلية التراجع. وهي منفصلة عن الحكم المرجعي؛ والموافقة الخارجية المطلوبة تصبح متطلبًا تشغيليًا مفتوحًا.",
  dimension: "البعد",
  finding: "النتيجة",
  note: "ملاحظة",
  externalAuthority: "الجهة المانحة للموافقة",
  record: "تسجيل",
  observations: "الملاحظات",
  observationExplainer: "ما لوحظ وقت حدوثه. تُسجل فقط أثناء تشغيل التجربة.",
  observedAt: "وقت الملاحظة",
  description: "الوصف",
  results: "النتائج المحللة",
  resultExplainer: "مشتقة من ملاحظات محددة أثناء التحليل.",
  method: "المنهج",
  summary: "الخلاصة",
  fromObservations: "من الملاحظات",
  interpretations: "التفسيرات",
  interpretationExplainer: "قراءتك للنتائج المحللة بالنسبة لفرضية التصميم.",
  outcome: "الخلاصة",
  statement: "النص",
  limitations: "الحدود",
  fromResults: "من النتائج",
  none: "لا شيء بعد.",
};
