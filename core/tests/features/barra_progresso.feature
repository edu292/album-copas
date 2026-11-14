# language: pt
Funcionalidade: Barra de progresso do álbum

  Cenário: Barra de progresso reflete figurinhas distintas coladas
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    E que estou autenticado como colecionador
    E que possuo 3 unidades de "Ronaldo", 1 unidade de "Cafu" e 0 de "Marcos"
    Quando eu acesso a página da edição de 2002
    Então o progresso exibido deve mostrar 2 figurinhas coladas do total da edição

  Cenário: Barra de progresso atualiza ao colar figurinha
    Dado que existe a seleção de 2002 com figurinhas cadastradas
    E que estou autenticado como colecionador
    Quando eu adiciono a figurinha "Marcos" ao meu álbum
    Então o progresso exibido deve mostrar 1 figurinhas coladas do total da edição
