try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None


class IncidentClassifier:
    """
    Classifieur base sur TF-IDF + similarite cosinus.
    Si scikit-learn n'est pas installe, il utilise un fallback simple
    base sur les mots-cles des categories.
    """

    PRIORITY_KEYWORDS = {
        'critical': [
            'inaccessible', 'panne totale', 'tous les utilisateurs',
            'serveur down', 'urgence', 'critique', 'bloque completement',
            'impossible de travailler', 'arret complet', 'data loss',
            'perte de donnees', 'securite', 'piratage', 'intrusion',
            'virus', 'ransomware', 'tout le monde', 'production arretee',
        ],
        'high': [
            'ne fonctionne pas', 'erreur', 'bloque', 'impossible',
            'urgent', 'rapide', 'plusieurs utilisateurs', 'impact important',
            'crash', 'plantage', 'acces refuse', 'mot de passe expire',
        ],
        'medium': [
            'lent', 'probleme', 'dysfonctionnement', 'parfois',
            'intermittent', 'difficulte', 'gene', 'ralentissement',
            'bug', 'anomalie', 'ne repond plus', 'deconnexion',
        ],
        'low': [
            'question', 'demande', 'information', 'amelioration',
            'suggestion', 'quand possible', 'pas urgent', 'mineur',
            'cosmetique', 'configuration', 'installation', 'mise a jour',
        ],
    }

    def __init__(self):
        if TfidfVectorizer is None:
            self.vectorizer = None
        else:
            self.vectorizer = TfidfVectorizer(
                analyzer='word',
                ngram_range=(1, 2),
                min_df=1,
                stop_words=None,
            )

    def _get_category_corpus(self, categories):
        corpus = []
        for category in categories:
            keywords = category.get_keywords_list()
            text = f"{category.name} {' '.join(keywords)}"
            corpus.append(text.lower())
        return corpus

    def _suggest_category_by_keywords(self, incident_text, categories):
        best_category = None
        best_score = 0

        for category in categories:
            keywords = [category.name.lower(), *category.get_keywords_list()]
            score = sum(
                1
                for keyword in keywords
                if keyword and keyword.lower() in incident_text
            )

            if score > best_score:
                best_category = category
                best_score = score

        return best_category

    def suggest_category(self, title, description, categories):
        if not categories:
            return None

        incident_text = f"{title} {description}".lower()

        if self.vectorizer is None or cosine_similarity is None:
            return self._suggest_category_by_keywords(incident_text, categories)

        corpus = self._get_category_corpus(categories)
        all_texts = corpus + [incident_text]

        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        except ValueError:
            return None

        category_vectors = tfidf_matrix[:-1]
        incident_vector = tfidf_matrix[-1]
        similarities = cosine_similarity(incident_vector, category_vectors).flatten()

        best_index = max(range(len(similarities)), key=lambda index: similarities[index])
        best_score = similarities[best_index]

        if best_score < 0.05:
            return None

        return categories[best_index]

    def suggest_priority(self, title, description):
        text = f"{title} {description}".lower()
        scores = {priority: 0 for priority in self.PRIORITY_KEYWORDS}

        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[priority] += 1

        best_priority = max(scores, key=scores.get)

        if scores[best_priority] == 0:
            return 'medium'

        return best_priority

    def classify(self, title, description, categories):
        return {
            'category': self.suggest_category(title, description, categories),
            'priority': self.suggest_priority(title, description),
        }


classifier = IncidentClassifier()
