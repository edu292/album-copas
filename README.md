# Album copas

## Onde as coisas estão?

- **core/models**: Onde os modelos do db ficam
- **core/urls**: Onde cadastra a url que leva á página
- **core/views**: Função que roda e retorna o render do template
- **templates/core**: Html tunado do django.

## Como rodar

```bash
uv sync
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py seed_album
uv run manage.py runserver 0.0.0.0:80
# se o windows chorar bota outra porta, mas aí vai ter que fazer localhost:porta
```

acessar http://localhost
