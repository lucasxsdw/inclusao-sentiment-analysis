🧠 Diário de Bordo da Inclusão - Módulo de IA
Este módulo é o "motor emocional" do sistema. É responsável por receber os desabafos dos alunos em português, interagir com modelos de Inteligência Artificial na nuvem e registar os sentimentos estruturados na base de dados.

🏗️ Arquitetura e Padrões de Desenho
Service Layer Pattern: A lógica de negócio e de integração externa está isolada no ficheiro sentimento_service.py, mantendo as Views do Django limpas.

Single Responsibility Principle (SRP): As funções estão estritamente divididas. Uma função traduz, outra comunica com a API e uma terceira orquestra o fluxo e guarda na base de dados.

Resiliência (Fail-Safe): A integração com a API externa possui blocos try/except robustos, timeouts definidos e não bloqueia o servidor caso o serviço da IA fique indisponível.

⚙️ Funcionalidades Implementadas
🌍 Tradução Nativa: Utilização da biblioteca deep-translator para converter as entradas de Português (PT-BR) para Inglês em tempo real, maximizando a precisão do modelo.

🤖 Inferência na Nuvem: Integração com a Inference API da Hugging Face utilizando o modelo j-hartmann/emotion-english-distilroberta-base.

🗺️ Mapeamento de Domínio: Tradução reversa automática através de dicionários (dict) para garantir que os dados sejam guardados em português (ex: fear → medo), facilitando a futura geração de relatórios.

🛡️ Auditoria em Produção: Substituição de prints genéricos pelo módulo nativo de logging do Python, permitindo o rastreio de erros de rede sem expor falhas ao utilizador final.