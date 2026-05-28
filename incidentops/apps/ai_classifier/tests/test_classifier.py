import pytest
from apps.ai_classifier.classifier import IncidentClassifier
from apps.tickets.factories import CategoryFactory


@pytest.mark.django_db
class TestIncidentClassifier:

    def setup_method(self):
        self.classifier = IncidentClassifier()

    def test_suggest_category_reseau(self):
        cat_reseau = CategoryFactory(
            name='Réseau',
            keywords='wifi, internet, connexion, réseau'
        )
        cat_materiel = CategoryFactory(
            name='Matériel',
            keywords='ordinateur, écran, clavier, panne'
        )
        categories = [cat_reseau, cat_materiel]

        result = self.classifier.suggest_category(
            title="Problème wifi",
            description="Je n'arrive pas à me connecter au réseau internet",
            categories=categories
        )
        assert result == cat_reseau

    def test_suggest_category_materiel(self):
        cat_reseau = CategoryFactory(
            name='Réseau',
            keywords='wifi, internet, connexion'
        )
        cat_materiel = CategoryFactory(
            name='Matériel',
            keywords='ordinateur, écran, clavier, panne matériel'
        )
        categories = [cat_reseau, cat_materiel]

        result = self.classifier.suggest_category(
            title="Écran cassé",
            description="Mon ordinateur ne s'allume plus, panne matériel",
            categories=categories
        )
        assert result == cat_materiel

    def test_suggest_priority_critical(self):
        priority = self.classifier.suggest_priority(
            title="Panne serveur",
            description="Le serveur est inaccessible pour tous les utilisateurs, urgence critique"
        )
        assert priority == 'critical'

    def test_suggest_priority_low(self):
        priority = self.classifier.suggest_priority(
            title="Demande d'information",
            description="Bonjour, j'ai une question sur la configuration, pas urgent"
        )
        assert priority == 'low'

    def test_suggest_priority_default_medium(self):
        priority = self.classifier.suggest_priority(
            title="abc",
            description="xyz"
        )
        assert priority == 'medium'

    def test_classify_returns_dict(self):
        cat = CategoryFactory(name='Test', keywords='test, exemple')
        result = self.classifier.classify('test incident', 'description test', [cat])
        assert 'category' in result
        assert 'priority' in result

    def test_no_categories_returns_none(self):
        result = self.classifier.suggest_category('titre', 'description', [])
        assert result is None