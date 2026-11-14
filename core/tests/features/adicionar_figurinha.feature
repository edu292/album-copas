# language: pt
Funcionalidade: Adicionar figurinhas ao álbum

  Cenário: Colecionador autenticado cola uma nova figurinha
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    E que estou autenticado como colecionador
    Quando eu adiciono a figurinha "Ronaldo" ao meu álbum
    Então a quantidade da figurinha "Ronaldo" no meu álbum deve ser 1

  Cenário: Colecionador autenticado adiciona uma figurinha repetida
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    E que estou autenticado como colecionador
    E que já possuo 1 unidade da figurinha "Ronaldo"
    Quando eu adiciono a figurinha "Ronaldo" ao meu álbum
    Então a quantidade da figurinha "Ronaldo" no meu álbum deve ser 2

  Cenário: Usuário anônimo não pode adicionar figurinhas
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    Quando um usuário não autenticado tenta adicionar a figurinha "Ronaldo"
    Então ele deve ser redirecionado para a página de login
