# language: pt
Funcionalidade: Filtrar jogadores por posição

  Cenário: Filtrar jogadores pela posição Goleiro
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    Quando eu filtro os jogadores de 2002 pela posição "GK"
    Então a página deve exibir "Marcos"
    E a página não deve exibir "Ronaldo"
    E a página não deve exibir "Cafu"
