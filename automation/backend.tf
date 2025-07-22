terraform {
  backend "azurerm" {
    resource_group_name  = "vida-home-dev"
    storage_account_name = "terraformstate2242"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
    use_azuread_auth     = false
  }
}
