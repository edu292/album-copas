import datetime
import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup, Tag
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from core.models import Sticker, Team

WIKI_API = 'https://pt.wikipedia.org/w/api.php'
HEADERS = {
    'User-Agent': 'AlbumDoPenta/1.0 (https://pt.wikipedia.org/wiki/User:AlbumDoPenta; eduskoroboatei@gmail.com) python-requests/2.32',
    'Referer': 'https://pt.wikipedia.org/',
}
MONTHS_PT = {
    m: i
    for i, m in enumerate(
        (
            'janeiro',
            'fevereiro',
            'março',
            'abril',
            'maio',
            'junho',
            'julho',
            'agosto',
            'setembro',
            'outubro',
            'novembro',
            'dezembro',
        ),
        1,
    )
}
EDITIONS = (
    (1958, 1, 'O primeiro título', ''),
    (1962, 2, 'O bicampeonato', ''),
    (1970, 3, 'O tricampeonato eterno', ''),
    (
        1994,
        4,
        'É tetra!',
        'https://midias.correiobraziliense.com.br/_midias/jpg/2022/10/20/1-26692588.jpg',
    ),
    (
        2002,
        5,
        'O pentacampeonato',
        'https://static1.purebreak.com.br/articles/9/10/77/09/@/477369-20-anos-da-copa-do-mundo-2002-veja-o-an-1200x0-3.jpg',
    ),
)
POS_MAP = {
    'G': Sticker.Position.GOALKEEPER,
    'GK': Sticker.Position.GOALKEEPER,
    'LD': Sticker.Position.RIGHT_BACK,
    'Z': Sticker.Position.CENTRE_BACK,
    'LE': Sticker.Position.LEFT_BACK,
    'V': Sticker.Position.DEFENSIVE_MIDFIELDER,
    'M': Sticker.Position.CENTRAL_MIDFIELDER,
    'MD': Sticker.Position.RIGHT_WINGER,
    'PD': Sticker.Position.RIGHT_WINGER,
    'ME': Sticker.Position.LEFT_WINGER,
    'PE': Sticker.Position.LEFT_WINGER,
    'A': Sticker.Position.STRIKER,
    'CA': Sticker.Position.STRIKER,
}

SKIP_IMG = (
    'logo',
    'flag_of',
    'bandeira',
    'kit_',
    'soccerball',
    'captain',
    'star',
    'ambox',
    'icon',
    'symbol',
    'brasão',
    'crest',
    '.svg',
)


class Command(BaseCommand):
    help = 'Popula o Álbum do Penta via MediaWiki API com validação estrita.'

    def handle(self, *args, **options):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        for year, stars, tagline, team_image_url in EDITIONS:
            team_title = f'Brasil_na_Copa_do_Mundo_FIFA_de_{year}'
            team_soup = self._fetch_soup(team_title)
            final_soup = self._fetch_soup(f'Final_da_Copa_do_Mundo_FIFA_de_{year}')
            cup_soup = self._fetch_soup(f'Copa_do_Mundo_FIFA_de_{year}')

            meta = self._parse_metadata(year, team_soup, cup_soup)
            players = self._parse_lineup(year, final_soup)
            pages = self._fetch_pages(
                [(team_title,)] + [p['candidates'] for p in players]
            )

            team_page = {
                **pages[team_title],
                'image_url': team_image_url or self._extract_team_photo(team_soup),
            }
            team, _ = Team.objects.update_or_create(
                year=year, defaults={'tagline': tagline, 'stars': stars, **meta}
            )
            self.stdout.write(self.style.SUCCESS(f'=== Brasil {year} ==='))

            self._upsert_sticker(
                team, 1, Sticker.Kind.TEAM, 'Seleção', None, False, team_page, set()
            )
            self.stdout.write(f'  BRA 01 · Seleção ({year})')

            for slot, p in enumerate(players, start=2):
                page = self._resolve_page(pages, p['candidates'])
                prior = set(
                    Sticker.objects.filter(
                        kind=Sticker.Kind.PLAYER, name=p['name'], team__year__lt=year
                    ).values_list('details', flat=True)
                )
                self._upsert_sticker(
                    team,
                    slot,
                    Sticker.Kind.PLAYER,
                    p['name'],
                    p['position'],
                    p['is_captain'],
                    page,
                    prior,
                )
                self.stdout.write(f'  BRA {slot:02d} · {p["name"]} ({p["position"]})')

        self.stdout.write(self.style.SUCCESS('Seed concluído com sucesso!'))

    def _fetch_soup(self, title: str) -> BeautifulSoup:
        resp = self.session.get(
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
        if not (html := resp.json().get('parse', {}).get('text', '')):
            raise CommandError(f'HTML não encontrado: {title}')
        return BeautifulSoup(html, 'html.parser')

    def _fetch_pages(self, candidate_groups: list[tuple[str, ...]]) -> dict[str, dict]:
        titles = list(dict.fromkeys(t for group in candidate_groups for t in group))
        pages = {}
        for i in range(0, len(titles), 20):
            batch = titles[i : i + 20]
            resp = self.session.get(
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
            q = resp.json().get('query', {})
            norm = {n['from']: n['to'] for n in q.get('normalized', [])}
            redir = {r['from']: r['to'] for r in q.get('redirects', [])}
            by_title = {
                p['title']: p for p in q.get('pages', []) if not p.get('missing')
            }

            for raw in batch:
                res = unquote(raw).replace('_', ' ')
                res = redir.get(norm.get(res, res), norm.get(res, res))
                if p := by_title.get(res):
                    ii_url = (p.get('imageinfo') or [{}])[0].get('url', '')
                    pages[raw] = {
                        'title': res,
                        'extract': p.get('extract', '').strip(),
                        'image_url': p.get('thumbnail', {}).get('source')
                        or p.get('original', {}).get('source')
                        or ii_url,
                    }
        return pages

    def _resolve_page(
        self, pages: dict[str, dict], candidates: tuple[str, ...]
    ) -> dict:
        for c in candidates:
            if (p := pages.get(c)) and p['extract'] and p['image_url']:
                return p
        raise CommandError(
            f'Página/imagem/resumo ausente na Wikipedia para: {candidates}'
        )

    def _parse_lineup(self, year: int, soup: BeautifulSoup) -> list[dict]:
        for table in soup.select('table'):
            rows = []
            for tr in table.find_all('tr'):
                text = tr.get_text(' ', strip=True).lower()
                if (
                    any(
                        k in text
                        for k in ('substituições', 'reservas', 'suplentes', 'treinador')
                    )
                    and rows
                ):
                    break
                tds = tr.find_all('td', recursive=False)
                if len(tds) >= 3:
                    pos_code, num, a = (
                        tds[0].get_text(strip=True).upper(),
                        tds[1].get_text(strip=True),
                        tds[2].find('a', href=re.compile(r'^/wiki/')),
                    )
                    if pos_code in POS_MAP and num.isdigit() and a:
                        rows.append((pos_code, tds[2], a))
                if len(rows) == 11:
                    break

            if len(rows) == 11 and any(
                gk in rows[0][2].get_text()
                for gk in ('Gilmar', 'Félix', 'Taffarel', 'Marcos')
            ):
                has_cm = any(r[0] == 'M' for r in rows)
                dm_assigned = any(r[0] == 'V' for r in rows) and has_cm
                players = []
                for pos_code, cell, a in rows:
                    pos = POS_MAP[pos_code]
                    if pos_code in ('V', 'M') and not dm_assigned:
                        pos, dm_assigned = Sticker.Position.DEFENSIVE_MIDFIELDER, True
                    elif pos_code == 'V' and not has_cm:
                        pos = Sticker.Position.CENTRAL_MIDFIELDER

                    name = a.get_text(strip=True)
                    base = name.replace(' ', '_')
                    players.append(
                        {
                            'name': name,
                            'candidates': (
                                unquote(a['href'].removeprefix('/wiki/')),
                                f'{base}_(futebolista)',
                                base,
                            ),
                            'position': pos,
                            'is_captain': bool(
                                cell.find(
                                    'img', alt=re.compile(r'capitão', re.IGNORECASE)
                                )
                                or cell.find(
                                    'a', title=re.compile(r'capitão', re.IGNORECASE)
                                )
                                or re.search(r'\(c\)', cell.get_text(), re.IGNORECASE)
                            ),
                        }
                    )
                return players
        raise CommandError(f'Escalação titular não encontrada na final de {year}.')

    def _parse_metadata(
        self, year: int, team_soup: BeautifulSoup, cup_soup: BeautifulSoup
    ) -> dict:
        def cell_val(soup: BeautifulSoup, *labels: str) -> str:
            for tr in soup.select('table tr'):
                cells = tr.find_all(['th', 'td'], recursive=False)
                if (
                    len(cells) >= 2
                    and cells[0].get_text(' ', strip=True).rstrip(':').lower() in labels
                ):
                    for sup in cells[1].select('sup'):
                        sup.decompose()
                    if val := re.sub(r'\s+', ' ', cells[1].get_text(' ', strip=True)):
                        return val
            return ''

        coach = cell_val(team_soup, 'técnico', 'treinador')
        host = cell_val(
            cup_soup, 'país', 'anfitrião', 'anfitriões', 'sede', 'local'
        ) or cell_val(team_soup, 'sede', 'anfitrião')

        heading = team_soup.find(id='Final') or cup_soup.find(id='Final')
        table = heading.find_next('table') if heading else None
        if not isinstance(table, Tag):
            raise CommandError(f'Tabela da final não encontrada para {year}.')

        row_cells = table.find('tr').find_all(['th', 'td'])
        top = [c.get_text(' ', strip=True) for c in row_cells]
        block = table.get_text(' ', strip=True)

        dm = re.search(
            rf'(\d{{1,2}})\s+de\s+({"|".join(MONTHS_PT)})(?:\s+de\s+(\d{{4}}))?',
            top[0] if top else block,
            re.IGNORECASE,
        )
        sm = re.search(r'(\d+)\s*[–\-×x]\s*(\d+)', top[2]) if len(top) > 3 else None
        if not dm or not sm:
            raise CommandError(f'Data ou placar da final ausente para {year}.')

        br_first = 'brasil' in top[1].lower()
        g1, g2 = (sm[1], sm[2]) if br_first else (sm[2], sm[1])
        score = f'{g1} × {g2}'
        if pm := re.search(r'\((\d+\s*[–\-]\s*\d+)\s*pên', block, re.IGNORECASE):
            score = f'{score} ({pm[1]} pên.)'

        for br in row_cells[-1].find_all('br'):
            br.replace_with('\n')
        stadium = row_cells[-1].get_text(' ', strip=True).split('\n')[0].strip()

        meta = {
            'host_country': host,
            'coach': coach,
            'final_date': datetime.date(
                int(dm[3] or year), MONTHS_PT[dm[2].lower()], int(dm[1])
            ),
            'final_opponent': top[3] if br_first else top[1],
            'final_score': score,
            'final_stadium': stadium,
        }
        if missing := [k for k, v in meta.items() if not v]:
            raise CommandError(f'Campos ausentes para {year}: {missing}')
        return meta

    def _extract_details(self, text: str, year: int, prior_texts: set[str]) -> str:
        cleaned = re.sub(r'^=+\s*.*?\s*=+$|\[\d+\]', '', text, flags=re.MULTILINE)
        split_rx = r'(?<=[.!?])\s+'
        prior = {
            s.strip() for b in prior_texts for s in re.split(split_rx, b) if s.strip()
        }

        era = [
            s
            for s in (s.strip() for s in re.split(split_rx, cleaned) if s.strip())
            if s not in prior
            and max((int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b', s)), default=0)
            <= year
        ]
        chosen = [s for s in era if str(year) in s or 'Copa' in s or 'Mundial' in s][
            :3
        ] or era[:3]
        if not chosen:
            raise CommandError(f'Sem detalhes inéditos até {year}.')
        return ' '.join(chosen)

    def _extract_team_photo(self, soup: BeautifulSoup) -> str:
        for img in soup.select(
            '.mw-parser-output table img, .mw-parser-output figure img'
        ):
            src = img.get('src') or ''
            if img.find_parent(class_='ambox') or any(
                t in src.lower() for t in SKIP_IMG
            ):
                continue
            if int(img.get('width') or 0) >= 180 and int(img.get('height') or 0) >= 100:
                if srcset := img.get('srcset'):
                    src = srcset.split(',')[-1].strip().split(' ')[0]
                return f'https:{src}' if src.startswith('//') else src
        return ''

    def _upsert_sticker(self, team, slot, kind, name, pos, is_cap, page, prior):
        try:
            details = self._extract_details(page['extract'], team.year, prior)
        except CommandError:
            soup = self._fetch_soup(page['title'])
            for t in soup.select(
                'table, sup, style, .mw-editsection, .navbox, .reflist'
            ):
                t.decompose()
            body = '\n'.join(p.get_text(' ', strip=True) for p in soup.select('p'))
            details = self._extract_details(body, team.year, prior)

        resp = self.session.get(page['image_url'], timeout=20)
        resp.raise_for_status()
        ext = page['image_url'].split('?')[0].rsplit('.', 1)[-1].lower()
        ext = ext if ext in {'jpg', 'jpeg', 'png', 'webp'} else 'jpg'

        sticker = Sticker.objects.filter(team=team, slot=slot).first() or Sticker(
            team=team, slot=slot
        )
        sticker.kind, sticker.name, sticker.position = kind, name, pos
        sticker.is_captain, sticker.details = is_cap, details
        sticker.image.save(f'{slot:02d}.{ext}', ContentFile(resp.content), save=False)
        sticker.full_clean()
        sticker.save()
