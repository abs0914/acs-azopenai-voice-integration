# Resource Group - Use existing resource group
data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}
