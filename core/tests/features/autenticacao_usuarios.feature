# language: pt
Funcionalidade: Autenticação de usuários

  Cenário: Colecionador realiza login com credenciais válidas
    Dado que existe o colecionador "joao" cadastrado com a senha "SenhaForte123!"
    Quando eu envio o formulário de login com usuário "joao" e senha "SenhaForte123!"
    Então devo estar autenticado como "joao"
    E devo ser redirecionado para a página inicial

  Cenário: Colecionador não consegue entrar com senha incorreta
    Dado que existe o colecionador "joao" cadastrado com a senha "SenhaForte123!"
    Quando eu envio o formulário de login com usuário "joao" e senha "SenhaErrada999"
    Então não devo estar autenticado

  Cenário: Colecionador realiza logout com sucesso
    Dado que estou autenticado como "joao"
    Quando eu realizo logout
    Então não devo estar autenticado
    E devo ser redirecionado para a página inicial
