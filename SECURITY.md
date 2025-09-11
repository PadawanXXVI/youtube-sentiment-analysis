# 🔒 Política de Segurança

Este documento descreve como lidar com questões de segurança relacionadas ao projeto **YouTube Sentiment Analysis**.  
Embora seja um projeto acadêmico, seguimos boas práticas para manter a integridade do código e dos dados.

---

## 📌 Relato de Vulnerabilidades

Se você identificar uma vulnerabilidade no código, dependências ou configuração do projeto:

1. **Não abra uma issue pública.**  
2. Envie um e-mail para a equipe do projeto:  
   - Anderson de Matos Guimarães – [anderson.m.guimaraes@icloud.com](mailto:anderson.m.guimaraes@icloud.com)  
3. Inclua no e-mail:  
   - Descrição detalhada do problema  
   - Passos para reproduzir  
   - Possíveis soluções ou sugestões  

A equipe revisará o relato e responderá em até **7 dias**.

---

## 🔐 Boas práticas de segurança

- **Chaves de API** (YouTube Data API v3) devem ser mantidas no arquivo `.env` (nunca commitadas no repositório).  
- Nunca exponha dados sensíveis (tokens, senhas, credenciais).  
- Utilize a pasta `data/` apenas para armazenar comentários públicos do YouTube (sem dados pessoais identificáveis).  
- Dependências devem ser sempre instaladas a partir do `requirements.txt` atualizado.  
- Revisar periodicamente vulnerabilidades nas bibliotecas utilizadas com:  
  ```
  pip list --outdated
  pip-audit
  ```

---

## 📊 Escopo da Segurança

Este projeto **não** lida com dados pessoais ou sensíveis de usuários.  
Apenas comentários públicos disponíveis na plataforma YouTube serão utilizados para análise.  

---

## 📬 Contato

Para qualquer questão de segurança, entre em contato diretamente com a equipe do projeto:  
- Anderson de Matos Guimarães  
- Gustavo Stefano Thomazinho  
- Renan Ost  
