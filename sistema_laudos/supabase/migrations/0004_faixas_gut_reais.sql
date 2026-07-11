-- Recalibra a faixa de prioridade GUT para o padrão REAL da Paula,
-- observado nas matrizes do Laudo 50/2026 assinado:
--   100, 80 -> Imediata | 48 -> Alta | 36, 27 -> Média |
--   18, 12, 8 -> Programada | 6 -> Monitoramento.
-- Coluna gerada não pode ser alterada: recria.
alter table laudos.anomalias drop column if exists faixa_prioridade;
alter table laudos.anomalias add column faixa_prioridade text generated always as (
  case
    when g * u * t >= 80 then 'Imediata'
    when g * u * t >= 40 then 'Alta'
    when g * u * t >= 20 then 'Média'
    when g * u * t >=  8 then 'Programada'
    else 'Monitoramento'
  end
) stored;
