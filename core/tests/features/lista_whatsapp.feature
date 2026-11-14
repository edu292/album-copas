# language: pt
Funcionalidade: Gerar uma lista de texto para WhatsApp

  Contexto:
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    E que estou autenticado como colecionador
    E que possuo 3 unidades de "Ronaldo", 1 unidade de "Cafu" e 0 de "Marcos"

  Cenário: Gerar lista de figurinhas faltando da edição de 2002
    Quando eu solicito a lista de WhatsApp do tipo "missing" para o ano 2002
    Então o texto gerado deve conter "*Álbum do Penta · Brasil 2002 (Faltando)*"
    E o texto gerado deve listar a figurinha faltando "Marcos"
    E o texto gerado não deve conter "Ronaldo"

  Cenário: Gerar lista de figurinhas repetidas para troca
    Quando eu solicito a lista de WhatsApp do tipo "dupes" para o ano 2002
    Então o texto gerado deve conter "*Álbum do Penta · Brasil 2002 (Repetidas para troca)*"
    E o texto gerado deve listar "Ronaldo" com 2 repetidas
    E o texto gerado não deve conter "Cafu"
