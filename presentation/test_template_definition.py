from presentation.template_definition_loader import TemplateDefinitionLoader


loader = TemplateDefinitionLoader()

template = loader.load(
    "templates/vocabulary/template_definition.json"
)

print(template)