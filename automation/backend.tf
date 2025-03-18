terraform {
  backend "azurerm" {
    resource_group_name  = "terraform"
    storage_account_name = "<your storage account name>"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
    use_azuread_auth     = false
  }
}
