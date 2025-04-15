# escala/utils.py
import calendar
from datetime import date


def gerar_calendario_mes(year, month, escalas_dict=None):
    """
    Gera uma lista de semanas, onde cada semana é uma lista de dicionários de dias.
    Cada dicionário de dia contém: numero_dia, is_current_month, escala_obj, data_completa.
    """
    if escalas_dict is None:
        escalas_dict = {}  # Evita erro se não for passado

    cal = calendar.Calendar(firstweekday=6)  # Começa no Domingo (Monday=0, Sunday=6)
    try:
        # Gera a matriz de dias para o mês/ano especificado
        month_days = cal.monthdayscalendar(year, month)
    except ValueError:  # Ano ou mês inválido
        return []  # Retorna lista vazia se não puder gerar

    weeks_data = []  # Lista para armazenar as semanas

    for week in month_days:
        week_data = []  # Lista para armazenar os dias da semana atual
        for day_num in week:
            is_current = day_num != 0  # 0 representa dias fora do mês atual
            current_day_date = None
            escala_obj = None

            if is_current:
                try:
                    # Cria o objeto date para o dia atual
                    current_day_date = date(year, month, day_num)
                    # Busca a escala no dicionário usando a data como chave
                    escala_obj = escalas_dict.get(current_day_date)
                except ValueError:
                    # Caso raro, mas pode acontecer se monthdayscalendar retornar algo inesperado
                    is_current = False
                    day_num = 0  # Reseta para garantir consistência

            # Adiciona as informações do dia à lista da semana
            week_data.append(
                {
                    "numero_dia": day_num,  # Número do dia (0 se fora do mês)
                    "is_current_month": is_current,  # Booleano indicando se pertence ao mês
                    "escala_obj": escala_obj,  # Objeto EscalaUsuario ou None
                    "data_completa": current_day_date,  # Objeto date ou None
                }
            )
        weeks_data.append(week_data)  # Adiciona a semana completa à lista de semanas

    return weeks_data
