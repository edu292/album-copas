# language: pt
Funcionalidade: Ordenar a lista de jogadores em ordem alfabética

  Cenário: Ordenar jogadores de A a Z
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    Quando eu acesso a edição de 2002 ordenada por "alpha"
    Então "Cafu" deve aparecer antes de "Marcos"
    E "Marcos" deve aparecer antes de "Rivaldo"
    E "Rivaldo" deve aparecer antes de "Ronaldo"
