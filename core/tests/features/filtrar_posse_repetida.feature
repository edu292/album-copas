# language: pt
Funcionalidade: Filtrar figurinhas por repetidas ou não repetidas

  Contexto:
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    E que estou autenticado como colecionador
    E que possuo 3 unidades de "Ronaldo", 1 unidade de "Cafu" e 0 de "Marcos"

  Cenário: Filtrar apenas figurinhas repetidas
    Quando eu filtro as figurinhas de 2002 pelo status "dupes"
    Então a página deve exibir "Ronaldo"
    E a página não deve exibir "Cafu"
    E a página não deve exibir "Marcos"

  Cenário: Filtrar apenas figurinhas coladas
    Quando eu filtro as figurinhas de 2002 pelo status "owned"
    Então a página deve exibir "Ronaldo"
    E a página deve exibir "Cafu"
    E a página não deve exibir "Marcos"

  Cenário: Filtrar apenas figurinhas faltando
    Quando eu filtro as figurinhas de 2002 pelo status "missing"
    Então a página deve exibir "Marcos"
    E a página não deve exibir "Ronaldo"
    E a página não deve exibir "Cafu"
