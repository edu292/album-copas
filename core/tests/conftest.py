import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Sticker, Team

User = get_user_model()


@pytest.fixture
def dummy_image():
    return SimpleUploadedFile('player.webp', b'RIFF....WEBP', content_type='image/webp')


@pytest.fixture
def team_2002(db):
    team, _ = Team.objects.get_or_create(
        year=2002,
        defaults={
            'host_country': 'Coreia do Sul / Japão',
            'coach': 'Luiz Felipe Scolari',
            'tagline': 'O Penta',
            'stars': 5,
            'final_date': datetime.date(2002, 6, 30),
            'final_opponent': 'Alemanha',
            'final_score': '2 x 0',
            'final_stadium': 'Estádio Internacional de Yokohama',
        },
    )
    return team


@pytest.fixture
def sample_stickers(team_2002, dummy_image):
    squad, _ = Sticker.objects.get_or_create(
        team=team_2002,
        slot=1,
        defaults={
            'kind': Sticker.Kind.TEAM,
            'name': 'Seleção Brasileira 2002',
            'details': 'Esquadrão campeão do mundo.',
            'image': dummy_image,
        },
    )
    marcos, _ = Sticker.objects.get_or_create(
        team=team_2002,
        slot=2,
        defaults={
            'kind': Sticker.Kind.PLAYER,
            'name': 'Marcos',
            'position': Sticker.Position.GOALKEEPER,
            'details': 'Goleiro titular em todos os jogos.',
            'image': dummy_image,
        },
    )
    cafu, _ = Sticker.objects.get_or_create(
        team=team_2002,
        slot=3,
        defaults={
            'kind': Sticker.Kind.PLAYER,
            'name': 'Cafu',
            'position': Sticker.Position.RIGHT_BACK,
            'is_captain': True,
            'details': 'Capitão do penta.',
            'image': dummy_image,
        },
    )
    ronaldo, _ = Sticker.objects.get_or_create(
        team=team_2002,
        slot=4,
        defaults={
            'kind': Sticker.Kind.PLAYER,
            'name': 'Ronaldo',
            'position': Sticker.Position.STRIKER,
            'details': 'Artilheiro da Copa com 8 gols.',
            'image': dummy_image,
        },
    )
    rivaldo, _ = Sticker.objects.get_or_create(
        team=team_2002,
        slot=5,
        defaults={
            'kind': Sticker.Kind.PLAYER,
            'name': 'Rivaldo',
            'position': Sticker.Position.CENTRAL_MIDFIELDER,
            'details': 'Camisa 10 decisivo.',
            'image': dummy_image,
        },
    )

    return {
        'squad': squad,
        'marcos': marcos,
        'cafu': cafu,
        'ronaldo': ronaldo,
        'rivaldo': rivaldo,
    }


@pytest.fixture
def collector_user(db):
    return User.objects.create_user(username='colecionador', password='SenhaForte123!')


@pytest.fixture
def ctx():
    """Mutable dictionary to share state across Given/When/Then steps."""
    return {}
