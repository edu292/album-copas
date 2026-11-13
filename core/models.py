import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from image_toolkit.fields import WebPImageField
from image_toolkit.storages import OverwriteFileSystemStorage

User = get_user_model()


def sticker_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    year = instance.team.year
    slot = f'{instance.slot:02d}'
    slug = 'team' if instance.is_team else slugify(instance.name)
    return f'stickers/{year}/{slot}-{slug}{ext}'


class Team(models.Model):
    year = models.PositiveSmallIntegerField(
        _('Ano'),
        unique=True,
    )
    host_country = models.CharField(
        _('País-Sede'),
        max_length=100,
    )
    coach = models.CharField(_('Treinador'), max_length=100)
    tagline = models.CharField(_('Chamada'), max_length=100, blank=True)
    stars = models.PositiveSmallIntegerField(_('Estrelas'), default=1)
    final_date = models.DateField(_('Data da Final'))
    final_opponent = models.CharField(_('Adversário da Final'))
    final_score = models.CharField(_('Placar da Final'), max_length=20)
    final_stadium = models.CharField(_('Estádio da Final'), max_length=120)

    class Meta:
        verbose_name = _('Seleção')
        verbose_name_plural = _('Seleções')

    def __str__(self):
        return f'{self.host_country} - {self.year}'


class Sticker(models.Model):
    class Kind(models.TextChoices):
        TEAM = 'SQUAD', _('Seleção')
        PLAYER = 'PLAYER', _('Jogador')

    class Position(models.TextChoices):
        GOALKEEPER = 'GK', _('Goleiro')
        CENTRE_BACK = 'CB', _('Zagueiro')
        RIGHT_BACK = 'RB', _('Lateral-Direito')
        LEFT_BACK = 'LB', _('Lateral-Esquerdo')
        DEFENSIVE_MIDFIELDER = 'CDM', _('Volante')
        CENTRAL_MIDFIELDER = 'CM', _('Meio-Campo')
        RIGHT_WINGER = 'RW', _('Ponta-Direita')
        LEFT_WINGER = 'LW', _('Ponta-Esquerda')
        STRIKER = 'ST', _('Centroavante')

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='stickers',
        verbose_name=_('Seleção'),
    )
    kind = models.CharField(
        _('Tipo'),
        max_length=6,
        choices=Kind.choices,
        default=Kind.PLAYER,
    )
    slot = models.PositiveSmallIntegerField(
        _('Posição no Álbum'),
    )
    name = models.CharField(('Nome do Jogador'), max_length=100, blank=True, null=True)
    details = models.TextField(
        ('Detalhes'),
    )
    image = WebPImageField(
        verbose_name=_('Foto'),
        upload_to=sticker_upload_path,
        storage=OverwriteFileSystemStorage,
    )
    position = models.CharField(
        _('Posição em Campo'),
        max_length=3,
        choices=Position.choices,
        blank=True,
        null=True,
    )
    is_captain = models.BooleanField(_('Capitão'), default=False)

    @property
    def is_team(self):
        return self.kind == self.Kind.TEAM

    @property
    def subtitle(self):
        if self.is_team:
            return f'Seleção de {self.team.year}'
        return self.get_position_display()

    def clean(self):
        super().clean()
        if self.is_team:
            if self.position or self.is_captain:
                raise ValidationError(
                    _(
                        'Figurinhas de esquadrão não possuem posição em campo ou capitania.'
                    )
                )
        elif not self.position:
            raise ValidationError(
                {'position': _('Jogadores precisam de uma posição em campo.')}
            )

    class Meta:
        verbose_name = _('Figurinha')
        verbose_name_plural = _('Figurinhas')
        constraints = (
            models.UniqueConstraint(
                fields=['team', 'slot'],
                name='unique_team_slot',
            ),
            models.UniqueConstraint(
                fields=['team'],
                condition=models.Q(kind='SQUAD'),
                name='unique_team_squad_sticker',
            ),
        )

    def __str__(self):
        return f'{self.name} ({self.team.host_country} #{self.slot})'


class UserSticker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stickers')
    sticker = models.ForeignKey(
        Sticker, on_delete=models.CASCADE, related_name='owners'
    )
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'sticker'], name='unique_user_sticker'
            ),
        )
