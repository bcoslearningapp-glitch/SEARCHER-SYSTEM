# Guide d'utilisation

*Traduction du guide de référence [`USER_GUIDE.md`](USER_GUIDE.md). En cas d'écart, la version anglaise fait foi.*

Ce guide suit un projet de recherche de la première idée jusqu'à une production approuvée et exportable. L'interface est disponible en anglais (`/en`), en français (`/fr`) et en arabe (`/ar`, de droite à gauche). Pour installer et démarrer le produit, voir la section **Run locally** du README. Les sauvegardes sont décrites dans [`docs/operations/BACKUP_RESTORE.md`](../operations/BACKUP_RESTORE.md).

Trois règles valent partout :
- **L'IA propose, vous décidez.** Rien de ce que produit l'IA ne devient canonique tant que vous ne l'avez pas accepté ou approuvé. Une approbation est toujours l'acte d'une personne.
- **L'état du projet fait office de mémoire.** Les conversations, non.
- **Chaque modification est auditée.** Les enregistrements que vous avez approuvés sont versionnés, jamais écrasés en silence.

## 1. Démarrer un projet (Bureau)

1. Sur la page d'accueil, créez un projet à partir d'une idée, d'un problème ou d'une question.
2. Le **Bureau** affiche :
   - la question courante et le statut du projet ;
   - le mode de recherche ;
   - les décisions qui vous attendent ;
   - la **file d'attention** (ce qui requiert ensuite une personne) ;
   - les notes.
3. Rédigez le **cadrage du problème**. La porte de cadrage liste ce qui manque. Si un modèle est configuré, *Rédiger avec l'IA* propose un cadrage.
4. **Approuvez** le cadrage. C'est une approbation explicite, motivée, qui fait passer le projet en recherche active.

Prenez des notes librement. Une note ne devient une affirmation, une hypothèse de travail ou une question que lorsque vous la saisissez comme telle.

## 2. Constituer la bibliothèque (Bibliothèque et Sources du projet)

- **Cataloguez** une œuvre et son édition, puis téléversez un fichier (PDF, texte, EPUB ou image). Les fichiers sont vérifiés d'après leur contenu, pas leur nom. Le texte est extrait page par page en arrière-plan.
- **Sources physiques, restreintes ou connues seulement par leurs métadonnées :** cataloguez-les quand même et ouvrez une **demande d'accès hybride**. Consignez l'extrait exact, un résumé ou une photo lorsque vous consultez la source.
- La **recherche** couvre toute la bibliothèque locale, avec des ancres de page. Lorsque la recherche sémantique est activée (ADR-025), elle trouve aussi des passages par le sens, en arabe, en français et en anglais. Les résultats indiquent quel type de recherche a été effectué.
- Les listes de sources longues sont **paginées**.
- **Bibliothèque fondamentale.** Le texte du Coran n'est jamais fourni ni généré par le produit. Une Autorité constitutionnelle importe et approuve un jeu de données publié (voir le README).

## 3. Affirmations, preuves et hypothèses (Laboratoire et Carte)

- **Affirmations :** donnez à chacune un énoncé et un type.
- Une **preuve** relie un extrait exact à une affirmation ou à une hypothèse, comme appui, contradiction, limite ou nuance. Une preuve candidate reste candidate tant que vous ne l'avez pas évaluée.
- Les **citations exactes** sont copiées depuis des passages de page vérifiés et ne peuvent pas être modifiées.
- Les **hypothèses** ont des versions immuables. Une nouvelle preuve peut rétrograder une hypothèse automatiquement ; rien ne la promeut en silence.
- **Contester** (IA, facultatif) cherche des contre-preuves et des explications alternatives. Les résultats sont des propositions.
- La **Carte** montre le problème central, les hypothèses, les questions ouvertes, les décisions et les blocages.

## 4. Plans de recherche (Recherche)

Un plan couvre les pistes d'appui, de contestation et d'explications alternatives.
- Les recherches portent d'abord sur la bibliothèque locale. Si un modèle est configuré et que la politique de divulgation du projet le permet, elles peuvent aussi utiliser la recherche web.
- Les résultats web deviennent des **pistes de sources**, jamais des preuves.
- C'est vous qui jugez la suffisance. Elle ne peut être déclarée qu'une fois les pistes de contre-preuve explorées.

## 5. Revue de référence

Sur une hypothèse, ouvrez une **revue de référence**. Elle sépare les couches : texte source, interprétation, inférence et jugement.
- Consignez un jugement humain. Une **réserve bloquante** crée une décision que vous devez trancher.
- La porte de référence s'appuie sur ces jugements avant que le travail de conception puisse avancer.

## 6. Conception et expériences (Conception, Expériences)

- **Conception :**
  - Rédigez des exigences reliées à leur origine.
  - Proposez des concepts.
  - Vérifiez la porte de préparation à la conception, puis choisissez vous-même un concept.
- **Expériences :**
  - Rédigez un protocole, puis réalisez la revue d'impact humain et obtenez l'approbation.
  - Menez l'expérience et consignez observations, résultats et interprétations. Ils restent distincts.
- Un **bilan d'apprentissage** clôt une expérience.

## 7. Connaissances locales (Connaissances)

- Faites progresser les enseignements une étape à la fois par la porte de promotion des connaissances.
- Les connaissances sensibles au temps reviennent dans la file d'attention lorsqu'elles doivent être revalidées.
- La réutilisation dans un autre projet est un jugement de transférabilité étiqueté, jamais une preuve.
- La page **Terminologie** contient les termes canoniques approuvés. Un contrôle de traduction signale les écarts de force des affirmations d'une langue à l'autre.

## 8. Productions (Productions)

1. **Composez** une production (rapport, dossier, carte des preuves, etc.) dans une langue et un mode :
   - LISIBLE ;
   - RÉFÉRENCÉ, avec étiquettes et références ;
   - AUDIT, avec une trace pour chaque affirmation.
2. **Lancez les contrôles d'intégrité.** Huit étapes vérifient affirmations, citations, citations exactes, couches de référence, terminologie, traduction, modifications et rendu.
   - Une version en échec (FAILED) ne peut pas être approuvée.
   - Les avertissements doivent être reconnus par vous.
3. **Approuvez** la version.
4. **Téléchargez-la** en Markdown, HTML, DOCX ou PDF. Les citations sont reproduites mot pour mot, et chaque PDF embarque `quotes.json` avec le texte exact des citations.

## 9. Partager et déplacer le travail

- **Exporter le paquet** (en-tête du projet) produit un Research Core Package muni de sommes de contrôle.
- **Importez-le** sur une autre installation depuis la page d'accueil. L'import n'élève jamais le niveau de confiance : les textes fondamentaux arrivent en attente de validation, et les fichiers retenus deviennent des entrées sans contenu (métadonnées seules).
- **Espace de travail** (facultatif, s'il est configuré) met en attente des enregistrements choisis dans un espace distant. La politique de divulgation du projet est vérifiée d'abord, et chaque tentative est conservée dans le manifeste de divulgation.

## 10. Réglages et fiabilité de l'IA

- **Politique IA du projet** (Bureau) : réglez le consentement au cloud, les profils de modèles autorisés et les budgets. Les projets confidentiels exigent un consentement explicite ; les projets restreints n'envoient jamais de contenu à une IA dans le cloud.
- **Fiabilité de l'IA** (lien depuis le Bureau) : montre le comportement observé des fournisseurs, les résultats des évaluations par rapport aux seuils approuvés, et l'**audit de l'installation** (citations exactes, intégrité du Coran et du Hadith, séparation des couches, autorisation des outils).
- **Si un fournisseur est indisponible :** les tâches IA échouent de façon visible et tout le reste continue de fonctionner. Aucune donnée du projet ne dépend d'un fournisseur.

## 11. Clore et rouvrir

- **Clore** un projet passe par la porte de clôture. Sont vérifiés : décisions bloquantes, expériences inachevées, preuves non évaluées et fiche de clôture.
- **Rouvrez-le** avec un motif déclencheur. La fiche de clôture est conservée.
