# language: pt
Funcionalidade: Cadastro de usuários

  Cenário: Novo colecionador cria uma conta com sucesso
    Quando eu envio o formulário de cadastro com usuário "joao", senha "SenhaForte123!" e confirmação "SenhaForte123!"
    Então o usuário "joao" deve existir no banco de dados
    E devo estar autenticado como "joao"
    E devo ser redirecionado para a página inicial

  Cenário: Cadastro falha quando as senhas não conferem
    Quando eu envio o formulário de cadastro com usuário "usuario_invalido", senha "SenhaForte123!" e confirmação "OutraSenha999!"
    Então o usuário "usuario_invalido" não deve existir no banco de dados
    E não devo estar autenticado
    E a resposta deve exibir erros de validação no formulário

  Cenário: Cadastro falha quando o nome de usuário já está em uso
    Dado que existe o colecionador "joao" cadastrado com a senha "SenhaForte123!"
    Quando eu envio o formulário de cadastro com usuário "joao", senha "SenhaForte123!" e confirmação "SenhaForte123!"
    Então não devo estar autenticado
    E a resposta deve exibir erros de validação no formulário
