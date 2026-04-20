# 📓 Diário de Bordo da Inclusão

> Plataforma de apoio emocional com Inteligência Artificial para alunos com necessidades específicas, desenvolvida para o **NAPNE — Núcleo de Apoio às Pessoas com Necessidades Específicas**.

<br>

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-6.x-092E20?style=for-the-badge&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-configurado-336791?style=for-the-badge&logo=postgresql)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-IA_Generativa-4285F4?style=for-the-badge&logo=google)
![HuggingFace](https://img.shields.io/badge/Hugging_Face-NLP-FFD21E?style=for-the-badge)

---

## 📌 Sobre o Projeto

O **Diário de Bordo da Inclusão** é uma ponte inteligente entre o aluno que precisa desabafar e a equipe de apoio da instituição.

Muitos alunos têm dificuldade de expressar suas emoções diretamente para um psicólogo ou coordenador. O sistema oferece um **espaço seguro, intuitivo e sem julgamentos** onde o aluno pode registrar como está se sentindo. Em paralelo, transforma esses relatos em dados estruturados, permitindo que o NAPNE identifique de forma proativa quais alunos precisam de mais atenção.

> ⚠️ O sistema **não atua como substituto de acompanhamento psicológico**. O chat é limitado a 5 mensagens e sempre encaminha o aluno para atendimento humano no NAPNE.

---

## 🖥️ Telas do Sistema

| Tela | Descrição |
|------|-----------|
| **Home Page** | Página de entrada com apresentação do sistema e acesso ao diário |
| **Home** | Painel principal do aluno após entrar na plataforma |
| **Seleção de Emoções** | Interface visual para o aluno escolher como está se sentindo |
| **Chat** | Sessão de conversa com a IA, limitada a 5 mensagens por sessão |

---

## 🔄 Fluxo da Aplicação

```
Aluno acessa → Seleciona emoção → Chat com IA (máx. 5 msg) → Encaminhamento ao NAPNE
                     ↓                        ↓
              Cria SessaoEmocional     Análise de sentimento
              e Diario no banco        salva no banco (HuggingFace)
                                               ↓
                                       Gemini gera resposta empática
```

---

## 🧠 Arquitetura de IA

O sistema utiliza dois modelos de IA com responsabilidades distintas:

### 🔬 Motor de Classificação — Hugging Face (NLP)
- **Modelo:** `j-hartmann/emotion-english-distilroberta-base`
- Classifica o texto em 7 emoções: `raiva`, `nojo`, `medo`, `alegria`, `neutro`, `tristeza`, `surpresa`
- **Camada de tradução automática:** PT-BR → EN antes da análise, garantindo alta precisão do modelo
- Resultado salvo no banco com score de confiança

### 💬 Motor Generativo — Google Gemini
- **Modelo:** `gemini-2.0-flash`
- Gera respostas empáticas baseadas na emoção detectada e no texto do aluno
- Opera com **System Prompt restrito**: nunca dá diagnósticos, nunca minimiza o problema
- Respostas curtas (máximo 2 frases) no estilo de mensagens de chat
- Possui fallback: se a API falhar, retorna uma resposta padrão acolhedora

---

## 🗂️ Estrutura do Projeto

```
inclusao-sentiment-analysis/
│
├── config/                  # Configurações globais do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── accounts/                # App de usuários (em desenvolvimento)
│   └── models.py            # Modelo Aluno
│
├── diario/                  # App principal do fluxo do aluno
│   ├── models.py            # SessaoEmocional, Diario, Pergunta, Resposta
│   ├── views.py             # HomeView, EmotionsView, salvar_emocao()
│   ├── urls.py
│   ├── templates/
│   │   └── diario/
│   │       ├── homePage.html
│   │       ├── home.html
│   │       └── emotions.html
│   └── static/
│
├── analise/                 # App de IA e análise de sentimentos
│   ├── models.py            # AnaliseResposta, AnaliseSessao
│   ├── views.py             # enviar_desabafo() — endpoint principal
│   ├── urls.py
│   ├── services/
│   │   ├── chat_service.py       # Integração com Google Gemini
│   │   └── sentimento_service.py # Integração com Hugging Face
│   └── templates/
│       └── analise/
│           └── chat.html
│
├── .env.example             # Variáveis de ambiente necessárias
├── requeriments.txt
└── manage.py
```

---

## 🔌 Documentação da API

### `POST /analise/api/chat/`

Recebe o desabafo do aluno, processa a análise de sentimento, salva no banco e retorna a resposta da IA.

**Request Body:**
```json
{
  "texto_resposta": "Estou muito ansioso com as provas finais, sinto que não vou conseguir."
}
```

**Response `200 OK`:**
```json
{
  "sucesso": true,
  "mensagem_aluno": "Estou muito ansioso com as provas finais, sinto que não vou conseguir.",
  "emocao_detectada": "medo",
  "resposta_assistente": "Esse peso que você está sentindo é muito real. O que está te deixando mais inseguro em relação aos seus estudos?",
  "fim_de_sessao": false
}
```

**Erros mapeados:**

| Código | Situação |
|--------|----------|
| `400` | Payload vazio ou JSON inválido |
| `400` | Sessão expirada (diário não encontrado) |
| `405` | Método não permitido (GET) |
| `500` | Erro interno — possui fallback, o usuário nunca fica sem resposta |

---

## ⚙️ Instalação e Configuração

### Pré-requisitos
- Python 3.12+
- PostgreSQL instalado e rodando
- Conta no [Google AI Studio](https://aistudio.google.com/) (chave Gemini)
- Conta na [Hugging Face](https://huggingface.co/) (token de acesso)

### Passo a passo

**1. Clone o repositório**
```bash
git clone https://github.com/lucasxsdw/inclusao-sentiment-analysis.git
cd inclusao-sentiment-analysis
```

**2. Crie e ative o ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requeriments.txt
```

**4. Configure as variáveis de ambiente**

Copie o arquivo de exemplo e preencha com suas credenciais:
```bash
cp .env.example .env
```

Edite o `.env`:
```env
SECRET_KEY=sua-chave-secreta-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

GEMINI_API_KEY=sua-chave-do-google-ai-studio
HF_TOKEN=seu-token-da-hugging-face

DATABASE_NAME=diario_inclusao
DATABASE_USER=postgres
DATABASE_PASSWORD=sua-senha
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

**5. Crie o banco de dados e rode as migrações**
```bash
python manage.py migrate
```

**6. Inicie o servidor**
```bash
python manage.py runserver
```

Acesse: [http://localhost:8000](http://localhost:8000)

---

## 🗺️ Roadmap

### ✅ Concluído
- [x] Modelagem de dados (SessaoEmocional, Diario, Resposta, AnaliseResposta)
- [x] Integração com Hugging Face para análise de sentimentos
- [x] Pipeline de tradução automática PT-BR → EN
- [x] Integração com Google Gemini para respostas empáticas
- [x] Endpoint da API `/analise/api/chat/`
- [x] Limite ético de 5 mensagens por sessão com encaminhamento ao NAPNE
- [x] Interface Frontend — HomPage, Home, Seleção de Emoções e Chat
- [x] Configuração de ambiente com `.env` e PostgreSQL

### 🔧 Em desenvolvimento
- [ ] Sistema de autenticação e perfil do aluno
- [ ] Painel do NAPNE — visualização de sessões e estatísticas emocionais
- [ ] Implementação de políticas de privacidade (LGPD)
- [ ] Deploy em servidor de produção

---

## 🛡️ Segurança e Privacidade

Este sistema lida com **dados emocionais sensíveis** de alunos, potencialmente menores de idade. As seguintes práticas estão implementadas ou planejadas:

- ✅ Segredos gerenciados via variáveis de ambiente (`.env`)
- ✅ Banco de dados PostgreSQL com credenciais externas ao código
- ✅ Limite de sessão de chat para evitar dependência do sistema
- ⏳ Autenticação de alunos (em desenvolvimento)
- ⏳ Conformidade com LGPD — consentimento, retenção e exclusão de dados (planejado)

---

## 🤝 Contexto Acadêmico

Projeto desenvolvido como **Trabalho de Conclusão de Curso (TCC)**, com foco em impacto social real. O sistema foi projetado para ser utilizado pelo NAPNE de instituições de ensino como ferramenta de apoio — não de substituição — ao acompanhamento psicológico profissional.

---
