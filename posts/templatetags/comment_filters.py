from django import template
register = template.Library()


@register.filter
def addUserClass(field, css):
    return field.as_widget(attrs={"class": css})
