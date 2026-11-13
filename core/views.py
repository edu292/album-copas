from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Sticker, Team, UserSticker


def _annotated_stickers(user, team, params=None):
    qs = team.stickers.all()
    if user.is_authenticated:
        qty_sq = UserSticker.objects.filter(
            user=user, sticker=models.OuterRef('pk')
        ).values('quantity')[:1]
        qs = qs.annotate(
            quantity=Coalesce(
                models.Subquery(qty_sq),
                models.Value(0),
                output_field=models.IntegerField(),
            )
        )
    else:
        qs = qs.annotate(quantity=models.Value(0, output_field=models.IntegerField()))

    qs = qs.annotate(
        tilt=(((models.F('slot') * 37) % 7) - 3) * models.Value(0.45),
    )

    if params:
        if q := params.get('q', '').strip():
            qs = qs.filter(name__icontains=q)
        if pos := params.get('position'):
            qs = qs.filter(position=pos)
        status = params.get('status')
        if status == 'owned':
            qs = qs.filter(quantity__gt=0)
        elif status == 'missing':
            qs = qs.filter(quantity=0)
        elif status == 'dupes':
            qs = qs.filter(quantity__gt=1)
        if params.get('sort') == 'alpha':
            qs = qs.order_by('name')

    return qs


def _spread_context(request, team):
    stickers = list(_annotated_stickers(request.user, team, request.GET))
    players = [s for s in stickers if not s.is_team]
    return {
        'team': team,
        'squad_sticker': next((s for s in stickers if s.is_team), None),
        'left_stickers': players[:3],
        'right_stickers': players[3:],
    }


def _progress_context(user, team):
    total = team.stickers.count()
    owned = (
        UserSticker.objects.filter(
            user=user, sticker__team=team, quantity__gt=0
        ).count()
        if user.is_authenticated
        else 0
    )
    return {'owned_count': owned, 'total_count': total}


def home(request: HttpRequest):
    first_team = Team.objects.order_by('year').first()
    if not first_team:
        raise Http404('Nenhuma edição cadastrada no álbum')

    return redirect('core:team_detail', year=first_team.year)


def team_detail(request, year):
    teams = Team.objects.all()
    team = get_object_or_404(teams, year=year)
    context = {
        'teams': teams,
        'positions': Sticker.Position.choices,
        **_spread_context(request, team),
        **_progress_context(request.user, team),
    }
    return render(request, 'core/team_detail.html', context)


def sticker_spread(request, year):
    team = get_object_or_404(Team, year=year)
    return render(request, 'core/partials/spread.html', _spread_context(request, team))


def sticker_modal(request, pk):
    sticker = get_object_or_404(Sticker.objects.select_related('team'), pk=pk)
    qty = (
        UserSticker.objects.filter(user=request.user, sticker=sticker)
        .values_list('quantity', flat=True)
        .first()
        or 0
        if request.user.is_authenticated
        else 0
    )
    return render(
        request,
        'core/components/sticker_modal.html',
        {'sticker': sticker, 'quantity': qty},
    )


@login_required
def whatsapp_modal(request):
    list_type = request.GET.get('type', 'missing')
    year = request.GET.get('year')
    is_dupes = list_type == 'dupes'

    if year:
        team = get_object_or_404(Team, year=year)
        qs = _annotated_stickers(request.user, team)
        qs = qs.filter(quantity__gt=1) if is_dupes else qs.filter(quantity=0)
        scope = f'Brasil {team.year}'
        lines = [
            f'• BRA {s.slot:02d} - {s.name}'
            + (f' (x{s.quantity - 1} repetida)' if is_dupes else '')
            for s in qs
        ]
    else:
        qty_sq = UserSticker.objects.filter(
            user=request.user, sticker=models.OuterRef('pk')
        ).values('quantity')[:1]
        qs = (
            Sticker.objects.select_related('team')
            .annotate(
                quantity=Coalesce(
                    models.Subquery(qty_sq),
                    models.Value(0),
                    output_field=models.IntegerField(),
                )
            )
            .order_by('team__year', 'slot')
        )
        qs = qs.filter(quantity__gt=1) if is_dupes else qs.filter(quantity=0)
        scope = 'Todas as Edições'
        lines = [
            f'• [{s.team.year}] BRA {s.slot:02d} - {s.name}'
            + (f' (x{s.quantity - 1} repetida)' if is_dupes else '')
            for s in qs
        ]

    header = (
        f'*Álbum do Penta · {scope} (Repetidas para troca)*'
        if is_dupes
        else f'*Álbum do Penta · {scope} (Faltando)*'
    )
    text = '\n'.join([header, *(lines or ['Nenhuma figurinha nesta lista.'])])

    return render(
        request,
        'core/components/whatsapp_modal.html',
        {'list_type': list_type, 'year': year, 'text': text},
    )


@login_required
@require_POST
def add_sticker(request, pk):
    sticker = get_object_or_404(Sticker.objects.select_related('team'), pk=pk)
    obj, _ = UserSticker.objects.get_or_create(user=request.user, sticker=sticker)
    UserSticker.objects.filter(pk=obj.pk).update(quantity=models.F('quantity') + 1)
    obj.refresh_from_db(fields=['quantity'])
    sticker.quantity = obj.quantity
    sticker.tilt = round((((sticker.slot * 37) % 7) - 3) * 0.45, 2)

    return render(
        request,
        'core/partials/sticker_oob.html',
        {'sticker': sticker, **_progress_context(request.user, sticker.team)},
    )


@login_required
@require_POST
def remove_sticker(request, pk):
    sticker = get_object_or_404(Sticker.objects.select_related('team'), pk=pk)
    obj, _ = UserSticker.objects.get_or_create(user=request.user, sticker=sticker)
    UserSticker.objects.filter(pk=obj.pk).update(quantity=models.F('quantity') - 1)
    obj.refresh_from_db(fields=['quantity'])
    sticker.quantity = obj.quantity
    sticker.tilt = round((((sticker.slot * 37) % 7) - 3) * 0.45, 2)

    return render(
        request,
        'core/partials/sticker_oob.html',
        {'sticker': sticker, **_progress_context(request.user, sticker.team)},
    )


@login_required
@require_POST
def update_sticker(request, pk):
    sticker = get_object_or_404(Sticker.objects.select_related('team'), pk=pk)
    try:
        qty = max(0, min(99, int(request.POST.get('quantity', 0))))
    except TypeError, ValueError:
        qty = 0

    if qty == 0:
        UserSticker.objects.filter(user=request.user, sticker=sticker).delete()
    else:
        UserSticker.objects.update_or_create(
            user=request.user, sticker=sticker, defaults={'quantity': qty}
        )

    sticker.quantity = qty
    sticker.tilt = round((((sticker.slot * 37) % 7) - 3) * 0.45, 2)
    return render(
        request,
        'core/partials/sticker_oob.html',
        {
            'sticker': sticker,
            'close_modal': True,
            **_progress_context(request.user, sticker.team),
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Conta criada!')
        return redirect('core:home')

    return render(request, 'registration/register.html', {'form': form})
