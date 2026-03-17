import json
from django.http import JsonResponse
from django.views.generic import TemplateView
from diario.models import SessaoEmocional, Diario, Resposta
from diario.models import Resposta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# pagina inicial 

class HomeView(TemplateView):
    template_name = 'diario/home.html'  

# registra sentimentos 
class EmotionsView(TemplateView):
    template_name = 'diario/emotions.html'


def salvar_emocao(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        emocao = data.get('emocao')

        if emocao:
            # 1️ Criar sessão
            sessao = SessaoEmocional.objects.create(
            emocao_selecionada=emocao,
            status_sessao='ativa',
            aluno=request.user.perfil_aluno if request.user.is_authenticated else None
        )

            # 💡 NOVIDADE: Mapeando a emoção para a primeira mensagem personalizada!
            mensagens_iniciais = {
                'muito_feliz': "Que incrível ver que você está muito feliz hoje! Quer me contar o que aconteceu?",
                'feliz': "Que bom que você está se sentindo feliz! Quer compartilhar o motivo?",
                'neutro': "Entendi. Como tem sido o seu dia até agora?",
                'triste': "Notei que você está se sentindo triste hoje. Quer conversar sobre o que está havendo?",
                'muito_triste': "Sinto muito que você esteja se sentindo assim. Estou aqui para te ouvir, no seu tempo. O que houve?",
                'ansioso': "Percebi que você está ansioso(a). Respire fundo... Quer me contar o que está te deixando assim?",
                'irritado': "Vejo que algo te deixou irritado(a). Quer desabafar sobre isso?",
                'cansado': "Você parece exausto(a). O que tem sugado as suas energias ultimamente?"
            }
            # Se a emoção não for achada, usa um texto padrão
            mensagem_personalizada = mensagens_iniciais.get(emocao, "Olá, estou aqui para te ouvir. Como você está?")

            # 2️ Criar diário automaticamente com a mensagem dinâmica
            diario = Diario.objects.create(
                sessao_emocional=sessao,
                mensagem_inicial_ia=mensagem_personalizada
            )

            # 3️ A MÁGICA DA SESSÃO: Guardar na "memória" do navegador para o Chat ler depois!
            request.session['diario_atual_id'] = diario.id
            request.session['emocao_inicial'] = emocao
            request.session['contagem_mensagens'] = 0  # Já preparando o seu limite de 5 perguntas!

            return JsonResponse({
                'status': 'success',
                'sessao_id': sessao.id,
                'diario_id': diario.id
            })

        return JsonResponse({'status': 'error'}, status=400)

    return JsonResponse({'status': 'error'}, status=405)


# template inical + apresentcao do sistema 
class homePageViews(TemplateView):
    template_name = 'diario/homePage.html'

# sobre 
class sobre(TemplateView):
    template_name = 'diario/sobre.html'



# Mapeamento de emoções para emojis
EMOCAO_EMOJI = {
    'muito_feliz': '😄',
    'feliz': '😊',
    'neutro': '😐',
    'triste': '😢',
    'muito_triste': '😭',
    'ansioso': '😰',
    'irritado': '😠',
    'cansado': '😴',
    'alegria': '😊',
    'tristeza': '😢',
    'medo': '😨',
    'raiva': '😠',
    'surpresa': '😲',
    'nojo': '🤢',
}

# Emoções que indicam atenção
EMOCOES_ATENCAO = ['triste', 'muito_triste', 'ansioso', 'irritado', 'tristeza', 'medo', 'raiva']


@login_required
def historico_emocional(request):
    try:
        aluno = request.user.perfil_aluno
    except Exception:
        aluno = None

    sessoes = []

    if aluno:
        sessoes_qs = SessaoEmocional.objects.filter(
            aluno=aluno
        ).order_by('-data_inicio')

        for sessao in sessoes_qs:
            # Busca o diário vinculado
            try:
                diario = sessao.diario
            except Exception:
                continue

            # Busca todas as respostas do diário com suas análises
            respostas = Resposta.objects.filter(
                diario=diario
            ).prefetch_related('analiseresposta')

            analises = []
            for resposta in respostas:
                try:
                    analise = resposta.analiseresposta
                    analises.append({
                        'sentimento': analise.sentimento_detectado or 'neutro',
                        'score': round((analise.score_sentimento or 0) * 100),
                        'texto': resposta.texto_resposta,
                    })
                except Exception:
                    pass

            # Emoção predominante da sessão (maior score)
            emocao_predominante = sessao.emocao_selecionada
            score_predominante = 0
            if analises:
                melhor = max(analises, key=lambda x: x['score'])
                emocao_predominante = melhor['sentimento']
                score_predominante = melhor['score']

            emoji = EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐')
            precisa_atencao = sessao.emocao_selecionada in EMOCOES_ATENCAO

            sessoes.append({
                'sessao': sessao,
                'diario': diario,
                'analises': analises,
                'emocao_predominante': emocao_predominante,
                'score_predominante': score_predominante,
                'emoji': emoji,
                'precisa_atencao': precisa_atencao,
            })

    return render(request, 'diario/historico.html', {
        'sessoes': sessoes,
        'total_sessoes': len(sessoes),
    })
