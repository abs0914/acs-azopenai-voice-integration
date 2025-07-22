# Azure Communication Service - Use existing vida-voicebot resource
data "azurerm_communication_service" "communication_service" {
  name                = "vida-voicebot"
  resource_group_name = data.azurerm_resource_group.rg.name
}

# Set the phone number as a local value since it already exists
locals {
  agent_phone_number = "+18449197485"
}

resource "null_resource" "assign_identity_acs" {
  depends_on = [data.azurerm_communication_service.communication_service]
  provisioner "local-exec" {
    command = "az communication identity assign --resource-group ${data.azurerm_resource_group.rg.name} --name ${data.azurerm_communication_service.communication_service.name} --system-assigned true"
  }
}
