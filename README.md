


# 📓 Diário de Bordo da inclusão - Análise de Sentimentos para Pessoas com Deficiência 
```markdown
> ⚠️ **Status do Projeto:** Em Desenvolvimento ativo (Work in Progress) 🏗️

O **Diário de Bordo da inclusão** é uma plataforma de apoio emocional voltada para o ambiente escolar. Seu objetivo é oferecer um espaço seguro e acolhedor onde os alunos possam desabafar. 

O sistema utiliza inteligência artificial para ler o relato do aluno, classificar a emoção predominante e gerar uma resposta empática, no formato de uma pergunta reflexiva, sem fornecer diagnósticos ou conselhos diretivos.

---

## 🚀 Arquitetura e Tecnologias

Este projeto foi construído com foco em resiliência, separação de responsabilidades e integração com serviços avançados de IA.

* **Linguagem & Framework:** Python 3, Django
* **Motor de Classificação de Sentimentos (Cérebro):** * Modelo: `j-hartmann/emotion-english-distilroberta-base` (via Hugging Face).
    * Mapeia o desabafo em 7 emoções: raiva, nojo, medo, alegria, neutro, tristeza e surpresa.
    * Possui uma camada de tradução automática (PT-BR -> EN) sob o capô para garantir alta precisão do modelo NLP.
* **Motor Gerativo de Respostas (Voz):** * Modelo: `gemini-2.5-flash` (via Google Gemini API / `google-genai`).
    * Utiliza Engenharia de Prompt restrita (System Prompt) para garantir que a IA atue como um conselheiro acolhedor, retornando respostas curtas, empáticas e seguras.

---

## 🔌 Documentação da API

A aplicação expõe um endpoint principal para comunicação com o Frontend.

### `POST /analise/api/chat/`

Recebe o desabafo do aluno, processa a análise de sentimento, salva no banco de dados e retorna a interação da IA.

**Request Body (JSON):**
```json
{
  "texto_resposta": "Estou muito ansioso com as provas finais, sinto que não estudei o suficiente e vou reprovar."
}

```

**Response (200 OK):**

```json
{
  "sucesso": true,
  "mensagem_aluno": "Estou muito ansioso com as provas finais, sinto que não estudei o suficiente e vou reprovar.",
  "emocao_detectada": "medo",
  "resposta_assistente": "Nossa, é muito compreensível sentir esse peso com as provas chegando. O que está te deixando mais inseguro em relação aos seus estudos?"
}

```

**Erros Mapeados:**

* `400 Bad Request`: Payload vazio ou formato JSON inválido.
* `405 Method Not Allowed`: Tentativa de acesso via GET.
* `500 Internal Server Error`: Falhas genéricas (possui sistema de Fallback para as IAs não deixarem o usuário sem resposta).

---

## 🛠️ Instalação e Configuração (Local)

1. Clone este repositório.
2. Crie e ative seu ambiente virtual (`python -m venv venv`).
3. Instale as dependências listadas:
```bash
pip install django google-genai
# Demais dependências do requirements.txt

```


4. Crie um arquivo `.env` na raiz do projeto e configure suas variáveis de ambiente:
```env
GEMINI_API_KEY=sua_chave_do_google_ai_studio_aqui

```


5. Realize as migrações do banco de dados:
```bash
python manage.py migrate

```


6. Inicie o servidor:
```bash
python manage.py runserver

```



---

## 🗺️ Roadmap / Próximos Passos

* [x] Estruturação da modelagem de dados no Django.
* [x] Integração com API de análise de sentimentos (Hugging Face).
* [x] Integração com LLM para respostas dinâmicas (Google Gemini).
* [x] Criação do endpoint da API (`/analise/api/chat/`).
* [ ] Construção da interface Frontend (HTML/JS com Fetch API).
* [ ] Implementação das políticas de segurança e privacidade (LGPD) no banco de dados.
* [ ] Sistema de autenticação e histórico do aluno.
  [ ] Lado dos servidores.

```

***

Esse documento já eleva o nível da apresentação do seu código no GitHub! 

```