import datetime
import re
from dataclasses import dataclass
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from core.models import Sticker, Team

WIKI_API = 'https://pt.wikipedia.org/w/api.php'
HEADERS = {
    'User-Agent': 'AlbumDoPenta/1.0 (https://pt.wikipedia.org/wiki/User:AlbumDoPenta; eduskoroboatei@gmail.com) python-requests/2.32',
    'Referer': 'https://pt.wikipedia.org/',
}

MONTHS_PT = {
    'janeiro': 1,
    'fevereiro': 2,
    'março': 3,
    'abril': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'outubro': 10,
    'novembro': 11,
    'dezembro': 12,
}


@dataclass(frozen=True)
class PlayerSeed:
    name: str
    position: str
    wiki_title: str = ''
    is_captain: bool = False

    @property
    def candidate_titles(self) -> tuple[str, ...]:
        if self.wiki_title:
            return (self.wiki_title,)
        base = self.name.replace(' ', '_')
        return (base, f'{base}_(futebolista)')


@dataclass(frozen=True)
class EditionSeed:
    year: int
    tagline: str
    stars: int
    players: tuple[PlayerSeed, ...]

    @property
    def team_wiki_title(self) -> str:
        return f'Brasil_na_Copa_do_Mundo_FIFA_de_{self.year}'

    @property
    def cup_wiki_title(self) -> str:
        return f'Copa_do_Mundo_FIFA_de_{self.year}'


EDITIONS: tuple[EditionSeed, ...] = (
    EditionSeed(
        year=1958,
        tagline='O primeiro título',
        stars=1,
        players=(
            PlayerSeed(
                'Gilmar', Sticker.Position.GOALKEEPER, 'Gylmar_dos_Santos_Neves'
            ),
            PlayerSeed('Djalma Santos', Sticker.Position.RIGHT_BACK),
            PlayerSeed('Bellini', Sticker.Position.CENTRE_BACK, is_captain=True),
            PlayerSeed('Orlando', Sticker.Position.CENTRE_BACK, 'Orlando_Peçanha'),
            PlayerSeed('Nílton Santos', Sticker.Position.LEFT_BACK),
            PlayerSeed('Zito', Sticker.Position.DEFENSIVE_MIDFIELDER),
            PlayerSeed('Didi', Sticker.Position.CENTRAL_MIDFIELDER, 'Valdir_Pereira'),
            PlayerSeed('Garrincha', Sticker.Position.RIGHT_WINGER),
            PlayerSeed('Vavá', Sticker.Position.STRIKER),
            PlayerSeed('Pelé', Sticker.Position.STRIKER),
            PlayerSeed(
                'Zagallo', Sticker.Position.LEFT_WINGER, 'Mário_Jorge_Lobo_Zagallo'
            ),
        ),
    ),
    EditionSeed(
        year=1962,
        tagline='O bicampeonato',
        stars=2,
        players=(
            PlayerSeed(
                'Gilmar', Sticker.Position.GOALKEEPER, 'Gylmar_dos_Santos_Neves'
            ),
            PlayerSeed('Djalma Santos', Sticker.Position.RIGHT_BACK),
            PlayerSeed(
                'Mauro',
                Sticker.Position.CENTRE_BACK,
                'Mauro_Ramos_de_Oliveira',
                is_captain=True,
            ),
            PlayerSeed('Zózimo', Sticker.Position.CENTRE_BACK),
            PlayerSeed('Nílton Santos', Sticker.Position.LEFT_BACK),
            PlayerSeed('Zito', Sticker.Position.DEFENSIVE_MIDFIELDER),
            PlayerSeed('Didi', Sticker.Position.CENTRAL_MIDFIELDER, 'Valdir_Pereira'),
            PlayerSeed('Garrincha', Sticker.Position.RIGHT_WINGER),
            PlayerSeed('Vavá', Sticker.Position.STRIKER),
            PlayerSeed('Amarildo', Sticker.Position.STRIKER),
            PlayerSeed(
                'Zagallo', Sticker.Position.LEFT_WINGER, 'Mário_Jorge_Lobo_Zagallo'
            ),
        ),
    ),
    EditionSeed(
        year=1970,
        tagline='O tricampeonato eterno',
        stars=3,
        players=(
            PlayerSeed('Félix', Sticker.Position.GOALKEEPER),
            PlayerSeed(
                'Carlos Alberto',
                Sticker.Position.RIGHT_BACK,
                'Carlos_Alberto_Torres',
                is_captain=True,
            ),
            PlayerSeed('Brito', Sticker.Position.CENTRE_BACK),
            PlayerSeed(
                'Piazza', Sticker.Position.CENTRE_BACK, 'Wilson_da_Silva_Piazza'
            ),
            PlayerSeed(
                'Everaldo', Sticker.Position.LEFT_BACK, 'Everaldo_Marques_da_Silva'
            ),
            PlayerSeed('Clodoaldo', Sticker.Position.DEFENSIVE_MIDFIELDER),
            PlayerSeed('Gérson', Sticker.Position.CENTRAL_MIDFIELDER),
            PlayerSeed('Jairzinho', Sticker.Position.RIGHT_WINGER),
            PlayerSeed('Tostão', Sticker.Position.STRIKER),
            PlayerSeed('Pelé', Sticker.Position.STRIKER),
            PlayerSeed('Rivellino', Sticker.Position.LEFT_WINGER, 'Roberto_Rivellino'),
        ),
    ),
    EditionSeed(
        year=1994,
        tagline='É tetra!',
        stars=4,
        players=(
            PlayerSeed('Taffarel', Sticker.Position.GOALKEEPER),
            PlayerSeed(
                'Jorginho', Sticker.Position.RIGHT_BACK, 'Jorge_de_Amorim_Campos'
            ),
            PlayerSeed('Aldair', Sticker.Position.CENTRE_BACK),
            PlayerSeed(
                'Márcio Santos',
                Sticker.Position.CENTRE_BACK,
                'Márcio_Roberto_dos_Santos',
            ),
            PlayerSeed(
                'Branco', Sticker.Position.LEFT_BACK, wiki_title='Branco_(futebolista)'
            ),
            PlayerSeed(
                'Mauro Silva',
                Sticker.Position.DEFENSIVE_MIDFIELDER,
                'Mauro_da_Silva_Gomes',
            ),
            PlayerSeed('Dunga', Sticker.Position.DEFENSIVE_MIDFIELDER, is_captain=True),
            PlayerSeed('Mazinho', Sticker.Position.CENTRAL_MIDFIELDER),
            PlayerSeed('Zinho', Sticker.Position.CENTRAL_MIDFIELDER),
            PlayerSeed('Bebeto', Sticker.Position.STRIKER),
            PlayerSeed('Romário', Sticker.Position.STRIKER),
        ),
    ),
    EditionSeed(
        year=2002,
        tagline='O pentacampeonato',
        stars=5,
        players=(
            PlayerSeed(
                'Marcos', Sticker.Position.GOALKEEPER, 'Marcos_Roberto_Silveira_Reis'
            ),
            PlayerSeed('Cafu', Sticker.Position.RIGHT_BACK, is_captain=True),
            PlayerSeed(
                'Lúcio', Sticker.Position.CENTRE_BACK, 'Lucimar_da_Silva_Ferreira'
            ),
            PlayerSeed('Roque Júnior', Sticker.Position.CENTRE_BACK),
            PlayerSeed('Edmílson', Sticker.Position.CENTRE_BACK),
            PlayerSeed(
                'Roberto Carlos',
                Sticker.Position.LEFT_BACK,
                wiki_title='Roberto_Carlos_(futebolista)',
            ),
            PlayerSeed('Gilberto Silva', Sticker.Position.DEFENSIVE_MIDFIELDER),
            PlayerSeed('Kléberson', Sticker.Position.CENTRAL_MIDFIELDER),
            PlayerSeed(
                'Ronaldinho', Sticker.Position.RIGHT_WINGER, 'Ronaldinho_Gaúcho'
            ),
            PlayerSeed('Rivaldo', Sticker.Position.LEFT_WINGER),
            PlayerSeed('Ronaldo', Sticker.Position.STRIKER, 'Ronaldo_Nazário'),
        ),
    ),
)


@dataclass(frozen=True)
class WikiPage:
    title: str
    extract: str
    image_url: str


def _fetch_html(session: requests.Session, title: str) -> BeautifulSoup:
    resp = session.get(
        WIKI_API,
        params={
            'action': 'parse',
            'format': 'json',
            'formatversion': '2',
            'redirects': '1',
            'page': unquote(title),
            'prop': 'text',
        },
        timeout=20,
    )
    resp.raise_for_status()
    html = resp.json().get('parse', {}).get('text', '')
    if not html:
        raise CommandError(f'HTML não encontrado na Wikipedia para: {title}')
    return BeautifulSoup(html, 'html.parser')


def _fetch_body_text(session: requests.Session, title: str) -> str:
    soup = _fetch_html(session, title)
    for tag in soup.select('table, sup, style, .mw-editsection, .navbox, .reflist'):
        tag.decompose()
    return '\n'.join(p.get_text(' ', strip=True) for p in soup.select('p'))


def _extract_team_photo_url(soup: BeautifulSoup) -> str:
    skip = (
        'logo',
        'flag_of',
        'bandeira',
        'kit_',
        'soccerball',
        'captain_sports',
        'star',
        'ambox',
        'icon',
        'symbol',
        'brasão',
        'crest',
        '.svg',
    )
    for img in soup.select('.mw-parser-output table img, .mw-parser-output figure img'):
        if img.find_parent(class_='ambox'):
            continue
        src = img.get('src') or ''
        if any(token in src.lower() for token in skip):
            continue
        width = int(img.get('width') or 0)
        height = int(img.get('height') or 0)
        if width < 180 or height < 100:
            continue
        srcset = img.get('srcset') or ''
        if srcset:
            src = srcset.split(',')[-1].strip().split(' ')[0]
        return f'https:{src}' if src.startswith('//') else src
    return ''


class Command(BaseCommand):
    help = 'Popula o Álbum do Penta via MediaWiki API com validação estrita.'

    def handle(self, *args, **options):
        session = requests.Session()
        session.headers.update(HEADERS)

        candidate_titles = (
            {ed.team_wiki_title for ed in EDITIONS}
            | {ed.cup_wiki_title for ed in EDITIONS}
            | {t for ed in EDITIONS for p in ed.players for t in p.candidate_titles}
        )
        pages = self._fetch_wiki_pages(session, sorted(candidate_titles))

        for edition in EDITIONS:
            team_page = self._require_page(pages, (edition.team_wiki_title,))
            team_soup = _fetch_html(session, edition.team_wiki_title)
            scraped = self._parse_edition_metadata(
                edition.year,
                team_soup,
                _fetch_html(session, edition.cup_wiki_title),
            )
            team_photo_url = _extract_team_photo_url(team_soup)
            if team_photo_url:
                team_page = WikiPage(
                    title=team_page.title,
                    extract=team_page.extract,
                    image_url=team_photo_url,
                )

            team, _ = Team.objects.update_or_create(
                year=edition.year,
                defaults={
                    'tagline': edition.tagline,
                    'stars': edition.stars,
                    **scraped,
                },
            )
            self.stdout.write(self.style.SUCCESS(f'=== Brasil {team.year} ==='))

            self._upsert_sticker(
                session=session,
                team=team,
                slot=1,
                kind=Sticker.Kind.TEAM,
                name='Seleção',
                position=None,
                is_captain=False,
                page=team_page,
                used_sentences=set(),
            )
            self.stdout.write(f'  BRA 01 · Seleção ({team.year})')

            for slot, player in enumerate(edition.players, start=2):
                player_page = self._require_page(pages, player.candidate_titles)
                used_sentences = set(
                    Sticker.objects.filter(
                        kind=Sticker.Kind.PLAYER,
                        name=player.name,
                        team__year__lt=team.year,
                    ).values_list('details', flat=True)
                )
                self._upsert_sticker(
                    session=session,
                    team=team,
                    slot=slot,
                    kind=Sticker.Kind.PLAYER,
                    name=player.name,
                    position=player.position,
                    is_captain=player.is_captain,
                    page=player_page,
                    used_sentences=used_sentences,
                )
                self.stdout.write(
                    f'  BRA {slot:02d} · {player.name} ({player.position})'
                )

        self.stdout.write(self.style.SUCCESS('Seed concluído com sucesso!'))

    def _require_page(
        self, pages: dict[str, WikiPage], candidates: tuple[str, ...]
    ) -> WikiPage:
        for title in candidates:
            if title in pages:
                return pages[title]
        raise CommandError(
            f'Página/imagem/resumo ausente na Wikipedia para candidatos: {candidates}'
        )

    def _fetch_wiki_pages(
        self, session: requests.Session, titles: list[str]
    ) -> dict[str, WikiPage]:
        pages: dict[str, WikiPage] = {}
        for i in range(0, len(titles), 20):
            batch = titles[i : i + 20]
            resp = session.get(
                WIKI_API,
                params={
                    'action': 'query',
                    'format': 'json',
                    'formatversion': '2',
                    'redirects': '1',
                    'titles': '|'.join(unquote(t) for t in batch),
                    'prop': 'extracts|pageimages',
                    'exintro': '1',
                    'explaintext': '1',
                    'exlimit': 'max',
                    'piprop': 'thumbnail|original',
                    'pithumbsize': '800',
                    'pilimit': 'max',
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

            query = data.get('query', {})
            normalized = {n['from']: n['to'] for n in query.get('normalized', [])}
            redirects = {r['from']: r['to'] for r in query.get('redirects', [])}
            by_title = {
                p['title']: p for p in query.get('pages', []) if not p.get('missing')
            }

            for raw_title in batch:
                resolved = unquote(raw_title).replace('_', ' ')
                resolved = normalized.get(resolved, resolved)
                resolved = redirects.get(resolved, resolved)
                page_data = by_title.get(resolved)
                if not page_data:
                    continue

                image_url = page_data.get('thumbnail', {}).get(
                    'source'
                ) or page_data.get('original', {}).get('source')
                extract = page_data.get('extract', '').strip()

                if not image_url or not extract:
                    continue

                pages[raw_title] = WikiPage(
                    title=resolved,
                    extract=extract,
                    image_url=image_url,
                )

        return pages

    def _parse_edition_metadata(
        self, year: int, team_soup: BeautifulSoup, cup_soup: BeautifulSoup
    ) -> dict:
        def table_value(soup: BeautifulSoup, *labels: str) -> str:
            targets = {lbl.lower() for lbl in labels}
            for tr in soup.select('table tr'):
                cells = tr.find_all(['th', 'td'], recursive=False)
                if len(cells) >= 2:
                    key = cells[0].get_text(' ', strip=True).rstrip(':').lower()
                    if key in targets:
                        for sup in cells[1].select('sup'):
                            sup.decompose()
                        val = cells[1].get_text(' ', strip=True)
                        if val:
                            return re.sub(r'\s+', ' ', val)
            return ''

        coach = table_value(team_soup, 'técnico', 'treinador')
        host_country = table_value(
            cup_soup, 'país', 'anfitrião', 'anfitriões', 'sede', 'local'
        ) or table_value(team_soup, 'sede', 'anfitrião')

        final_heading = team_soup.find(id='Final') or cup_soup.find(id='Final')
        if not final_heading:
            raise CommandError(f'Seção Final não encontrada na Wikipedia para {year}.')

        match_table = final_heading.find_next('table')
        if not match_table:
            raise CommandError(f'Tabela da final não encontrada para {year}.')

        rows = match_table.find_all('tr')
        top_cells = [
            c.get_text(' ', strip=True) for c in rows[0].find_all(['th', 'td'])
        ]
        block_text = match_table.get_text(' ', strip=True)

        raw_date = top_cells[0] if top_cells else block_text
        date_match = re.search(
            rf'(\d{{1,2}})\s+de\s+({"|".join(MONTHS_PT)})(?:\s+de\s+(\d{{4}}))?',
            raw_date,
            flags=re.IGNORECASE,
        )
        if not date_match:
            raise CommandError(f'Data da final não encontrada para {year}.')
        final_date = datetime.date(
            int(date_match.group(3) or year),
            MONTHS_PT[date_match.group(2).lower()],
            int(date_match.group(1)),
        )

        t1, score_raw, t2 = top_cells[1], top_cells[2], top_cells[3]
        brazil_is_t1 = 'brasil' in t1.lower()
        final_opponent = t2 if brazil_is_t1 else t1

        score_match = re.search(r'(\d+)\s*[–\-×x]\s*(\d+)', score_raw)
        if not score_match:
            raise CommandError(f'Placar da final não encontrado para {year}.')
        g1, g2 = score_match.group(1), score_match.group(2)
        if not brazil_is_t1:
            g1, g2 = g2, g1
        final_score = f'{g1} × {g2}'
        pen_match = re.search(r'\((\d+\s*[–\-]\s*\d+)\s*pên', block_text, re.IGNORECASE)
        if pen_match:
            final_score = f'{final_score} ({pen_match.group(1)} pên.)'

        stadium_cell = rows[0].find_all(['th', 'td'])[-1]
        for br in stadium_cell.find_all('br'):
            br.replace_with('\n')
        final_stadium = stadium_cell.get_text(' ', strip=True).split('\n')[0].strip()

        missing = [
            k
            for k, v in {
                'coach': coach,
                'host_country': host_country,
                'final_opponent': final_opponent,
                'final_stadium': final_stadium,
            }.items()
            if not v
        ]
        if missing:
            raise CommandError(
                f'Campos ausentes no scraping da Wikipedia para {year}: {missing}'
            )

        return {
            'host_country': host_country,
            'coach': coach,
            'final_date': final_date,
            'final_opponent': final_opponent,
            'final_score': final_score,
            'final_stadium': final_stadium,
        }

    def _extract_era_details(
        self, extract: str, year: int, prior_texts: set[str]
    ) -> str:
        cleaned = re.sub(r'^=+\s*.*?\s*=+$', '', extract, flags=re.MULTILINE)
        cleaned = re.sub(r'\[\d+\]', '', cleaned)

        prior_sentences = {
            s.strip()
            for block in prior_texts
            for s in re.split(r'(?<=[.!?])\s+', block)
            if s.strip()
        }
        sentences = [
            s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()
        ]

        era_filtered = []
        for sentence in sentences:
            years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', sentence)]
            if years and max(years) > year:
                continue
            if sentence in prior_sentences:
                continue
            era_filtered.append(sentence)

        cup_specific = [
            s for s in era_filtered if str(year) in s or 'Copa' in s or 'Mundial' in s
        ]
        chosen = cup_specific[:3] or era_filtered[:3]
        if not chosen:
            raise CommandError(
                f'Não foi possível extrair detalhes inéditos até {year} a partir do texto da Wikipedia.'
            )
        return ' '.join(chosen)

    def _upsert_sticker(
        self,
        session: requests.Session,
        team: Team,
        slot: int,
        kind: str,
        name: str,
        position: str | None,
        is_captain: bool,
        page: WikiPage,
        used_sentences: set[str],
    ) -> None:
        try:
            details = self._extract_era_details(page.extract, team.year, used_sentences)
        except CommandError:
            full_text = _fetch_body_text(session, page.title)
            details = self._extract_era_details(full_text, team.year, used_sentences)

        resp = session.get(page.image_url, timeout=20)
        resp.raise_for_status()
        if not resp.content:
            raise CommandError(
                f'Download de imagem vazio para {name} ({page.image_url})'
            )

        ext = page.image_url.split('?')[0].rsplit('.', 1)[-1].lower()
        if ext not in {'jpg', 'jpeg', 'png', 'webp'}:
            ext = 'jpg'

        sticker = Sticker.objects.filter(team=team, slot=slot).first() or Sticker(
            team=team, slot=slot
        )
        sticker.kind = kind
        sticker.name = name
        sticker.position = position
        sticker.is_captain = is_captain
        sticker.details = details
        sticker.image.save(f'{slot:02d}.{ext}', ContentFile(resp.content), save=False)
        sticker.full_clean()
        sticker.save()
