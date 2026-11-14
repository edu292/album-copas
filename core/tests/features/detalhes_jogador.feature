# language: pt
Funcionalidade: Exibir detalhes do jogador

  Cenário: Abrir modal com biografia e status de capitão do jogador
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    Quando eu acesso o modal da figurinha "Cafu"
    Então o modal deve exibir "Cafu"
    E o modal deve exibir "Capitão"
    E o modal deve exibir os detalhes cadastrados do jogador "Cafu"
