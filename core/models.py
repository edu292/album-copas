from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    year = models.PositiveSmallIntegerField(unique=True)
    host_country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.host_country} - {self.year}"

class Sticker(models.Model):
    name = models.CharField(max_length=100)
    details = models.TextField()
    image = models.ImageField(upload_to='stickers/') # Edu favor mexer nisso aqui
    posicao = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class TeamPlayer(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    sticker = models.ForeignKey(Sticker, on_delete=models.CASCADE)
    slot = models.PositiveSmallIntegerField()

    class Meta:
        # Garante as regras UNIQUE(team_id, slot) e CHECK 1-11 do seu diagrama
        constraints = [
            models.UniqueConstraint(fields=['team', 'slot'], name='unique_team_slot'),
            models.CheckConstraint(
                check=models.Q(slot__gte=1) & models.Q(slot__lte=11),
                name='check_slot_range'
            )
        ]

class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sticker = models.ForeignKey(Sticker, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'sticker')