from django import template
register = template.Library()


@register.filter
def addPostClass(field, css):
    return field.as_widget(attrs={"class": css})
