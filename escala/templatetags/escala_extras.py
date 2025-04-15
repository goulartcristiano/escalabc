# escala/templatetags/escala_extras.py

from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Permite acessar um item de dicionário usando uma variável como chave.
    Funciona de forma mais confiável com chaves complexas como objetos date.
    Retorna None se a chave não for encontrada ou se o input não for um dicionário.
    """
    if not isinstance(dictionary, dict):
        return None
    # Usa o método .get() do dicionário Python, que é robusto.
    return dictionary.get(key)
