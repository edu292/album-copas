from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Team(models.Model):
    year = models.PositiveSmallIntegerField(
        verbose_name=_('Ano'),
        unique=True,
    )
    host_country = models.CharField(
        verbose_name=_('País-Sede'),
        max_length=100,
    )

    class Meta:
        verbose_name = _('Seleção')
        verbose_name_plural = _('Seleções')

    def __str__(self):
        return f'{self.host_country} - {self.year}'


class Sticker(models.Model):
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
    slot = models.PositiveSmallIntegerField(
        verbose_name=_('Posição no Álbum'),
    )
    name = models.CharField(
        verbose_name=_('Nome do Jogador'),
        max_length=100,
    )
    details = models.TextField(
        verbose_name=_('Detalhes'),
    )
    image = models.ImageField(
        verbose_name=_('Foto'),
        upload_to='stickers/',
    )
    position = models.CharField(
        verbose_name=_('Posição em Campo'),
        max_length=3,
        choices=Position.choices,
    )

    class Meta:
        verbose_name = _('Figurinha')
        verbose_name_plural = _('Figurinhas')
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'slot'],
                name='unique_team_slot',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.team.host_country} #{self.slot})'


class UserSticker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stickers')
    sticker = models.ForeignKey(
        Sticker, on_delete=models.CASCADE, related_name='owners'
    )
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'sticker'], name='unique_user_sticker'
            )
        ]
