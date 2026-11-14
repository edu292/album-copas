# language: pt
Funcionalidade: Pesquisar figurinhas

  Cenário: Buscar jogador pelo nome parcial
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    Quando eu pesquiso por "Ron" na edição de 2002
    Então a página deve exibir "Ronaldo"
    E a página não deve exibir "Cafu"
