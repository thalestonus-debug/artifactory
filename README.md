# artifactory

Local para códigos motores de processos — um **catálogo de plugins do Claude**, organizado
por **frente de trabalho**. Cada frente é um plugin independente com suas próprias skills,
scripts, exemplos e testes.

## Frentes disponíveis

| Frente | O que faz | Skills |
|---|---|---|
| [`viagens`](plugins/viagens) | A partir de dias e locais, cota avião, ônibus, carro alugado, Airbnb e Booking e compara cenários | `planejar-viagem`, `cotar-transporte`, `cotar-hospedagem`, `comparar-cenarios` |

## Como usar no Claude Code

```bash
/plugin marketplace add thalestonus-debug/artifactory
```

```bash
/plugin install viagens@artifactory
```

Depois é só pedir em linguagem natural, por exemplo:

> Planeja uma viagem de 7 dias saindo de São Paulo para Rio de Janeiro e Paraty, 2 pessoas.

## Estrutura

```
artifactory/
├── .claude-plugin/marketplace.json   # catálogo: lista todas as frentes
├── plugins/
│   ├── _modelo/                      # esqueleto copiado para cada nova frente
│   └── viagens/                      # uma frente = um plugin
│       ├── .claude-plugin/plugin.json
│       ├── skills/<skill>/SKILL.md   # instruções que o Claude segue
│       ├── skills/<skill>/scripts/   # cálculos determinísticos (Python, só stdlib)
│       ├── exemplos/
│       └── tests/
├── ferramentas/
│   ├── nova_frente.py                # cria e registra uma nova frente
│   ├── validar.py                    # confere manifestos, catálogo e SKILL.md
│   └── testar_tudo.sh                # validação + testes de todas as frentes
└── .github/workflows/ci.yml          # roda testar_tudo.sh em todo push/PR
```

## Abrir uma nova frente

```bash
python3 ferramentas/nova_frente.py financas "Controle de gastos e investimentos" pessoal
```

Isso copia `plugins/_modelo` para `plugins/financas`, preenche nome e descrição e registra
a frente no catálogo. Depois:

1. Renomeie `skills/nome-da-skill` e escreva o `SKILL.md` (o `description` é o que faz o
   Claude acionar a skill — descreva o que faz e quando usar).
2. Coloque cálculos e regras fixas em `scripts/`, com testes em `tests/`.
3. Adicione a frente à tabela acima.
4. Rode `./ferramentas/testar_tudo.sh` antes de enviar.

## Convenções

- Nomes de frentes e skills: minúsculas com hífen (`gestao-obras`, `cotar-hospedagem`).
- Uma skill = uma responsabilidade. Fluxos completos ficam numa skill orquestradora que chama as outras.
- Scripts em Python 3 só com biblioteca padrão, lendo/escrevendo JSON — nada para instalar.
- Toda mudança de comportamento de um plugin sobe o `version` no `plugin.json` e no catálogo.
