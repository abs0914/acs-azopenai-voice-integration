#Speech, CognitiveServices - Use existing vida-voice-live resource
data "azurerm_cognitive_account" "CognitiveServices" {
  name                = "vida-voice-live"
  resource_group_name = data.azurerm_resource_group.rg.name
}
