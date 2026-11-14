from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_bdd import given, parsers, scenarios, then, when

from core.models import Sticker, UserSticker

User = get_user_model()

scenarios('features')


def _get_sticker(name: str) -> Sticker:
    return Sticker.objects.get(name=name)


@given('que existe a seleção de 2002 com figurinhas cadastradas')
def setup_team_and_stickers(team_2002, sample_stickers):
    return sample_stickers


@given(
    parsers.parse(
        'que existe o colecionador "{username}" cadastrado com a senha "{password}"'
    )
)
def create_named_collector(db, username, password):
    User.objects.get_or_create(username=username)
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    return user


@given('que estou autenticado como colecionador')
def login_as_collector(client, collector_user):
    client.force_login(collector_user)


@given(parsers.parse('que estou autenticado como "{username}"'))
def login_as_named_user(db, client, username):
    user, _ = User.objects.get_or_create(username=username)
    client.force_login(user)


@given(parsers.parse('que já possuo {qty:d} unidade da figurinha "{name}"'))
@given(parsers.parse('que já possuo {qty:d} unidades da figurinha "{name}"'))
def set_single_sticker_qty(collector_user, qty, name):
    sticker = _get_sticker(name)
    UserSticker.objects.update_or_create(
        user=collector_user, sticker=sticker, defaults={'quantity': qty}
    )


@given(
    parsers.parse(
        'que possuo {q1:d} unidades de "{n1}", {q2:d} unidade de "{n2}" e {q3:d} de "{n3}"'
    )
)
def set_multiple_stickers_qty(collector_user, q1, n1, q2, n2, q3, n3):
    for name, qty in [(n1, q1), (n2, q2), (n3, q3)]:
        if qty > 0:
            UserSticker.objects.update_or_create(
                user=collector_user,
                sticker=_get_sticker(name),
                defaults={'quantity': qty},
            )


@when(parsers.parse('eu adiciono a figurinha "{name}" ao meu álbum'))
def add_sticker_action(client, ctx, name):
    sticker = _get_sticker(name)
    ctx['response'] = client.post(reverse('core:add_sticker', args=[sticker.pk]))


@when(parsers.parse('um usuário não autenticado tenta adicionar a figurinha "{name}"'))
def anon_add_sticker(client, ctx, name):
    sticker = _get_sticker(name)
    ctx['response'] = client.post(reverse('core:add_sticker', args=[sticker.pk]))


@when(parsers.parse('eu pesquiso por "{query}" na edição de {year:d}'))
def search_stickers(client, ctx, query, year):
    ctx['response'] = client.get(reverse('core:team_detail', args=[year]), {'q': query})


@when(parsers.parse('eu filtro as figurinhas de {year:d} pelo status "{status}"'))
def filter_by_status(client, ctx, year, status):
    ctx['response'] = client.get(
        reverse('core:team_detail', args=[year]), {'status': status}
    )


@when(parsers.parse('eu filtro os jogadores de {year:d} pela posição "{position}"'))
def filter_by_position(client, ctx, year, position):
    ctx['response'] = client.get(
        reverse('core:team_detail', args=[year]), {'position': position}
    )


@when(
    parsers.parse(
        'eu envio o formulário de cadastro com usuário "{username}", senha "{password}" e confirmação "{confirm_password}"'
    )
)
def submit_registration(db, client, ctx, username, password, confirm_password):
    ctx['response'] = client.post(
        reverse('core:register'),
        {
            'username': username,
            'password1': password,
            'password2': confirm_password,
        },
    )


@when(
    parsers.parse(
        'eu envio o formulário de login com usuário "{username}" e senha "{password}"'
    )
)
def submit_named_login(client, ctx, username, password):
    ctx['response'] = client.post(
        reverse('login'),
        {'username': username, 'password': password},
    )


@when('eu realizo logout')
def submit_logout(client, ctx):
    ctx['response'] = client.post(reverse('logout'))


@when(parsers.parse('eu acesso a página da edição de {year:d}'))
def visit_team_detail(client, ctx, year):
    ctx['response'] = client.get(reverse('core:team_detail', args=[year]))


@when(parsers.parse('eu acesso o modal da figurinha "{name}"'))
def open_sticker_modal(client, ctx, name):
    sticker = _get_sticker(name)
    ctx['response'] = client.get(reverse('core:sticker_modal', args=[sticker.pk]))


@when(
    parsers.parse(
        'eu solicito a lista de WhatsApp do tipo "{list_type}" para o ano {year:d}'
    )
)
def request_whatsapp_list(client, ctx, list_type, year):
    ctx['response'] = client.get(
        reverse('core:whatsapp_modal'), {'type': list_type, 'year': year}
    )


@then(parsers.parse('o texto gerado deve listar a figurinha faltando "{name}"'))
def assert_whatsapp_missing_sticker(ctx, name):
    sticker = _get_sticker(name)
    expected_line = f'• BRA {sticker.slot:02d} - {sticker.name}'
    assert expected_line in ctx['response'].content.decode()


@then(parsers.parse('o texto gerado deve listar "{name}" com {dupes:d} repetidas'))
def assert_whatsapp_dupe_sticker(ctx, name, dupes):
    sticker = _get_sticker(name)
    expected_line = f'• BRA {sticker.slot:02d} - {sticker.name} (x{dupes} repetida)'
    assert expected_line in ctx['response'].content.decode()


@when(parsers.parse('eu acesso a edição de {year:d} ordenada por "{sort}"'))
def visit_sorted_team(client, ctx, year, sort):
    ctx['response'] = client.get(
        reverse('core:team_detail', args=[year]), {'sort': sort}
    )


@then(
    parsers.parse(
        'a quantidade da figurinha "{name}" no meu álbum deve ser {expected:d}'
    )
)
def check_sticker_quantity(collector_user, name, expected):
    us = UserSticker.objects.get(user=collector_user, sticker=_get_sticker(name))
    assert us.quantity == expected


@then('a resposta deve conter a atualização da figurinha')
def check_oob_response(ctx):
    assert ctx['response'].status_code == 200
    assert 'hx-swap-oob="true"' in ctx['response'].content.decode()


@then('ele deve ser redirecionado para a página de login')
def check_redirect_to_login(ctx):
    assert ctx['response'].status_code == 302
    assert reverse('login') in ctx['response'].url


@then(parsers.parse('a página deve exibir "{text}"'))
@then(parsers.parse('o modal deve exibir "{text}"'))
@then(parsers.parse('o texto gerado deve conter "{text}"'))
def assert_text_present(ctx, text):
    assert ctx['response'].status_code == 200
    assert text in ctx['response'].content.decode()


@then(parsers.parse('o modal deve exibir os detalhes cadastrados do jogador "{name}"'))
def assert_sticker_details_present(ctx, name):
    sticker = _get_sticker(name)
    assert sticker.details in ctx['response'].content.decode()


@then(parsers.parse('a página não deve exibir "{text}"'))
@then(parsers.parse('o texto gerado não deve conter "{text}"'))
def assert_text_absent(ctx, text):
    assert ctx['response'].status_code == 200
    assert text not in ctx['response'].content.decode()


@then(parsers.parse('o usuário "{username}" deve existir no banco de dados'))
def assert_user_created(username):
    assert User.objects.filter(username=username).exists()


@then(parsers.parse('o usuário "{username}" não deve existir no banco de dados'))
def assert_user_does_not_exist(username):
    assert not User.objects.filter(username=username).exists()


@then('devo ser redirecionado para a página inicial')
def assert_redirected_home(ctx):
    assert ctx['response'].status_code == 302
    assert ctx['response'].url == reverse('core:home')


@then('a resposta deve exibir erros de validação no formulário')
def assert_form_errors(ctx):
    assert ctx['response'].status_code == 200
    assert 'form-errors' in ctx['response'].content.decode()


@then(parsers.parse('devo estar autenticado como "{username}"'))
def assert_authenticated_as(client, username):
    user = User.objects.get(username=username)
    assert client.session.get('_auth_user_id') == str(user.pk)


@then('não devo estar autenticado')
def assert_not_authenticated(client):
    assert '_auth_user_id' not in client.session


@then('a barra superior deve exibir o botão de sair do colecionador')
def assert_logout_button_visible(ctx, collector_user):
    assert f'Sair ({collector_user.username})' in ctx['response'].content.decode()


@then(
    parsers.parse(
        'o progresso exibido deve mostrar {owned:d} figurinhas coladas do total da edição'
    )
)
def assert_progress_value(ctx, team_2002, owned):
    total = team_2002.stickers.count()
    assert f'{owned}/{total}' in ctx['response'].content.decode()


@then(parsers.parse('"{first}" deve aparecer antes de "{second}"'))
def assert_order(ctx, first, second):
    html = ctx['response'].content.decode()
    assert html.index(first) < html.index(second)
