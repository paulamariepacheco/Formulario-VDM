-- Seed idempotente do Laudo Nº 50/2026 — Edifício Otoni (fixture de teste).
-- Espelha dados/laudo_50_2026.json. Reexecutar recria o laudo do zero.
-- ATENÇÃO: textos e valores G/U/T são exemplos plausíveis — substituir pelos reais.
set search_path to laudos, public;

do $$
declare
  v_laudo uuid;
  a_sub2 uuid; a_gar uuid; a_ter uuid; a_fac uuid; a_res uuid;
  an1 uuid; an2 uuid; an3 uuid; an4 uuid; an5 uuid; an6 uuid;
begin
  delete from laudos.laudos where numero = '50/2026';  -- cascade limpa filhos

  insert into laudos.laudos (numero, tipo, cliente_nome, cliente_cnpj_cpf, endereco,
                             data_emissao, status, datas_diligencia, acompanhamento)
  values ('50/2026', 'condominial_nao_judicial', 'Condomínio do Edifício Otoni',
          '00.000.000/0001-00', 'Rua Otoni, nº 000 — Bairro Centro, Belo Horizonte/MG',
          '2026-07-10', 'em_redacao', array['12/06/2026','19/06/2026'], 'Síndico — Sr. Murilo')
  returning id into v_laudo;

  insert into laudos.ambientes (laudo_id, nome, pavimento, ordem) values
    (v_laudo, '2º Subsolo', '2º Subsolo', 1) returning id into a_sub2;
  insert into laudos.ambientes (laudo_id, nome, pavimento, ordem) values
    (v_laudo, 'Garagem (laje de cobertura)', '1º Subsolo', 2) returning id into a_gar;
  insert into laudos.ambientes (laudo_id, nome, pavimento, ordem) values
    (v_laudo, 'Hall Térreo', 'Térreo', 3) returning id into a_ter;
  insert into laudos.ambientes (laudo_id, nome, pavimento, ordem) values
    (v_laudo, 'Fachada Frontal', 'Externo', 4) returning id into a_fac;
  insert into laudos.ambientes (laudo_id, nome, pavimento, ordem) values
    (v_laudo, 'Casa de Bombas / Reservatório Inferior', '2º Subsolo', 5) returning id into a_res;

  insert into laudos.anomalias (laudo_id, ambiente_id, ordem, sistema_construtivo, titulo,
    descricao_fenomenologica, mecanismo, causa_provavel, consequencias, origem_taxonomia,
    vicio_ou_falha_manutencao, gr, g, u, t, alerta_juridico, status)
  values
    (v_laudo, a_fac, 1, 'impermeabilização e drenagem',
     'Jardineira da fachada frontal com impermeabilização comprometida',
     'Constatou-se na jardineira da fachada frontal a presença de manchas de umidade, eflorescências e destacamento do revestimento na face inferior adjacente, com escorrimento persistente para os panos de parede internos.',
     'Percolação de água pela camada de substrato em razão da ausência ou ruptura da manta de impermeabilização e da deficiência do sistema de drenagem.',
     'Impermeabilização com vida útil esgotada e/ou executada sem rodapé de arremate e sem dreno adequado.',
     'Deterioração progressiva do revestimento, risco de corrosão de armaduras e potencial destacamento de material sobre a via.',
     'construtiva', 'indeterminado', 3, 5, 5, 4, true, 'rascunho') returning id into an1;
  insert into laudos.anomalias (laudo_id, ambiente_id, ordem, sistema_construtivo, titulo,
    descricao_fenomenologica, mecanismo, causa_provavel, consequencias, origem_taxonomia,
    vicio_ou_falha_manutencao, gr, g, u, t, alerta_juridico, status)
  values
    (v_laudo, a_sub2, 2, 'estrutura',
     'Fissuras em viga de concreto armado do 2º subsolo',
     'Verificou-se fissuração mapeada e trinca de abertura relevante em viga de concreto armado do 2º subsolo, com indícios de exposição de armadura.',
     'Ingresso de agentes agressivos pela fissura, favorecendo despassivação e corrosão da armadura.',
     'Infiltração persistente associada a possível deficiência de cobrimento e/ou sobrecarga.',
     'Redução da capacidade resistente do elemento estrutural, com risco à segurança.',
     'adquirida', 'indeterminado', 3, 5, 4, 4, true, 'rascunho') returning id into an2;
  insert into laudos.anomalias (laudo_id, ambiente_id, ordem, sistema_construtivo, titulo,
    descricao_fenomenologica, mecanismo, causa_provavel, consequencias, origem_taxonomia,
    vicio_ou_falha_manutencao, gr, g, u, t, alerta_juridico, status)
  values
    (v_laudo, a_gar, 3, 'impermeabilização e drenagem',
     'Infiltração na laje de cobertura da garagem',
     'Manchas de umidade, estalactites e pingamento na face inferior da laje de cobertura da garagem.',
     'Percolação de água pluvial por falhas na impermeabilização e arremates deficientes.',
     'Sistema de impermeabilização sem manutenção e caimentos insuficientes.',
     'Comprometimento estético/funcional e risco de corrosão de armaduras a médio prazo.',
     'funcional', 'falha_manutencao', 2, 4, 3, 3, false, 'rascunho') returning id into an3;
  insert into laudos.anomalias (laudo_id, ambiente_id, ordem, sistema_construtivo, titulo,
    descricao_fenomenologica, mecanismo, causa_provavel, consequencias, origem_taxonomia,
    vicio_ou_falha_manutencao, gr, g, u, t, alerta_juridico, status)
  values
    (v_laudo, a_ter, 4, 'vedações e alvenarias',
     'Umidade ascendente em parede do hall térreo',
     'Faixa de umidade ascendente até cerca de 60 cm da base da parede, com eflorescências e destacamento do revestimento.',
     'Ascensão capilar de água do solo pela alvenaria por ausência de barreira horizontal.',
     'Corte de umidade inexistente ou deteriorado na base da parede.',
     'Degradação do revestimento e da pintura, com recorrência caso não tratada a origem.',
     'construtiva', 'vicio_construtivo', 2, 3, 3, 4, false, 'rascunho') returning id into an4;
  insert into laudos.anomalias (laudo_id, ambiente_id, ordem, sistema_construtivo, titulo,
    descricao_fenomenologica, mecanismo, causa_provavel, consequencias, origem_taxonomia,
    vicio_ou_falha_manutencao, gr, g, u, t, alerta_juridico, status)
  values
    (v_laudo, a_res, 5, 'instalações hidráulicas',
     'Sinais de vazamento no reservatório inferior',
     'Manchas de umidade e gotejamento na parede externa do reservatório inferior.',
     'Perda de estanqueidade por deterioração da impermeabilização interna e/ou fissuração.',
     'Impermeabilização interna do reservatório com vida útil esgotada.',
     'Desperdício de água tratada, risco de contaminação e patologias em elementos vizinhos.',
     'funcional', 'indeterminado', 2, 4, 4, 3, false, 'rascunho') returning id into an5;
  insert into laudos.anomalias (laudo_id, ambiente_id, ordem, sistema_construtivo, titulo,
    descricao_fenomenologica, mecanismo, causa_provavel, consequencias, origem_taxonomia,
    vicio_ou_falha_manutencao, gr, g, u, t, alerta_juridico, status)
  values
    (v_laudo, a_gar, 6, 'revestimentos e pisos',
     'Destacamento de rejunte no piso da garagem',
     'Perda de rejuntamento e destacamento pontual de placas cerâmicas em trecho do piso.',
     'Movimentação térmica e ausência de juntas de dessolidarização.',
     'Especificação/execução do rejunte incompatível com a solicitação de tráfego.',
     'Progressão do destacamento e risco de infiltração pontual pelas juntas.',
     'construtiva', 'vicio_construtivo', 1, 2, 2, 2, false, 'rascunho') returning id into an6;

  insert into laudos.fotos (laudo_id, anomalia_id, ambiente_id, ordem, legenda) values
    (v_laudo, an1, a_fac, 1, 'vista da jardineira com destacamento do revestimento e eflorescências'),
    (v_laudo, an2, a_sub2, 2, 'trinca em viga de concreto com indício de exposição de armadura'),
    (v_laudo, an3, a_gar, 3, 'manchas de umidade e estalactites na face inferior da laje'),
    (v_laudo, an4, a_ter, 4, 'faixa de umidade ascendente com bolhas na pintura'),
    (v_laudo, an5, a_res, 5, 'gotejamento na parede externa do reservatório inferior'),
    (v_laudo, an6, a_gar, 6, 'perda de rejunte e destacamento de placas cerâmicas');
end $$;
