# ------------------------------------------------------------------------------------------------------
# Deploy application insights
# ------------------------------------------------------------------------------------------------------
module "applicationinsights" {
  source           = "./modules/applicationinsights"
  location         = var.location
  rg_name          = data.azurerm_resource_group.rg.name
  environment_name = var.environment
  workspace_id     = module.loganalytics.LOGANALYTICS_WORKSPACE_ID
  tags             = local.default_tags
  resource_token   = "${local.name_prefix}-appinsights"
}

# ------------------------------------------------------------------------------------------------------
# Deploy log analytics
# ------------------------------------------------------------------------------------------------------
module "loganalytics" {
  source         = "./modules/loganalytics"
  location       = var.location
  rg_name        = data.azurerm_resource_group.rg.name
  tags           = local.default_tags
  resource_token = "${local.name_prefix}-loganalytics"
}

# ------------------------------------------------------------------------------------------------------
# Deploy app service plan
# ------------------------------------------------------------------------------------------------------
module "appserviceplan" {
  source         = "./modules/appserviceplan"
  location       = var.location
  rg_name        = data.azurerm_resource_group.rg.name
  tags           = local.default_tags
  resource_token = "${local.name_prefix}-appserviceplan"
  sku_name       = "B3"
}
# ------------------------------------------------------------------------------------------------------

data "archive_file" "api_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../api"
  output_path = "${path.module}/api_zip.zip"
  excludes    = [".vscode", "__pycache__"]
}

# ------------------------------------------------------------------------------------------------------
# Deploy app service api
# ------------------------------------------------------------------------------------------------------
module "api" {
  depends_on = [azurerm_cognitive_deployment.openai_deployments,
    azurerm_cosmosdb_sql_container.call_session_container,
    data.azurerm_communication_service.communication_service,
  azurerm_redis_cache.redis]

  source             = "./modules/appservicepython"
  location           = var.location
  rg_name            = data.azurerm_resource_group.rg.name
  resource_token     = "${local.name_prefix}-api-${random_string.unique.result}"
  tags               = merge(local.default_tags, { "api" = "api" })
  service_name       = "api"
  appservice_plan_id = module.appserviceplan.APPSERVICE_PLAN_ID
  app_settings = {
    SCM_DO_BUILD_DURING_DEPLOYMENT        = "true"
    APPLICATIONINSIGHTS_CONNECTION_STRING = module.applicationinsights.APPLICATIONINSIGHTS_CONNECTION_STRING
    #ACS
    ACS_CONNECTION_STRING      = data.azurerm_communication_service.communication_service.primary_connection_string
    COGNITIVE_SERVICE_ENDPOINT = data.azurerm_cognitive_account.CognitiveServices.endpoint
    AGENT_PHONE_NUMBER         = local.agent_phone_number
    VOICE_NAME                 = "en-US-AvaMultilingualNeural"
    # Azure OpenAI
    AZURE_OPENAI_SERVICE_KEY           = azurerm_cognitive_account.openai.primary_access_key
    AZURE_OPENAI_SERVICE_ENDPOINT      = azurerm_cognitive_account.openai.endpoint
    AZURE_OPENAI_DEPLOYMENT_MODEL_NAME = azurerm_cognitive_deployment.openai_deployments["gpt-4o"].model[0].name
    AZURE_OPENAI_DEPLOYMENT_MODEL      = azurerm_cognitive_deployment.openai_deployments["gpt-4o"].model[0].name
    OPENAI_ASSISTANT_ID                = "asst_dEODj1Hu6Z68Ebggl13DAHPv"
    # Azure AI Voice Live API
    AZURE_VOICE_LIVE_ENDPOINT          = "https://vida-voice-live.cognitiveservices.azure.com/"
    AZURE_VOICE_LIVE_API_KEY           = var.azure_voice_live_api_key
    AZURE_VOICE_LIVE_DEPLOYMENT        = "gpt-4o-realtime-preview"
    AZURE_VOICE_LIVE_REGION            = "eastus2"
    VIDA_VOICE_BOT_ASSISTANT_ID        = "asst_dEODj1Hu6Z68Ebggl13DAHPv"
    # Application Settings
    CALLBACK_URI_HOST   = "https://${local.name_prefix}-api-${random_string.unique.result}.azurewebsites.net"
    CALLBACK_EVENTS_URI = "https://${local.name_prefix}-api-${random_string.unique.result}.azurewebsites.net/api/callbacks"
    END_SILENCE_TIMEOUT = "0.4"

    COSMOS_DB_DATABASE_NAME  = azurerm_cosmosdb_sql_database.call_session_db.name
    COSMOS_DB_CONTAINER_NAME = azurerm_cosmosdb_sql_container.call_session_container.name
    COSMOS_DB_URL            = azurerm_cosmosdb_account.call_session_account.endpoint
    COSMOS_DB_KEY            = azurerm_cosmosdb_account.call_session_account.primary_key

    REDIS_URL      = azurerm_redis_cache.redis.hostname
    REDIS_PASSWORD = azurerm_redis_cache.redis.primary_access_key
    # Security and Performance Settings
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
    WEBSITES_CONTAINER_START_TIME_LIMIT = "1800"
  }
  health_check_path = "/api/health"
  app_command_line  = local.api_command_line
  identity = [{
    type = "SystemAssigned"
  }]

}


# Configure CORS with specific allowed origins for security
resource "null_resource" "api_set_allow_origins" {
  depends_on = [module.api]
  provisioner "local-exec" {
    # Allow Azure Communication Services and specific domains
    command = "az webapp config appsettings set --resource-group ${data.azurerm_resource_group.rg.name} --name ${module.api.APPSERVICE_NAME} --settings API_ALLOW_ORIGINS='https://*.azurewebsites.net,https://*.azure.com,https://localhost:*'"
  }
}

resource "null_resource" "deploy_app" {
  depends_on = [null_resource.api_set_allow_origins]
  provisioner "local-exec" {
    command = "az webapp deployment source config-zip --resource-group ${data.azurerm_resource_group.rg.name} --name ${module.api.APPSERVICE_NAME} --src ${data.archive_file.api_zip.output_path}"
  }
  # triggers = {
  #   always = "${timestamp()}"
  # }
}

# Assign Cognitive Services Contributor role to the Web App
resource "azurerm_role_assignment" "cognitive_services_contributor" {
  depends_on                       = [module.api]
  scope                            = azurerm_cognitive_account.openai.id
  role_definition_name             = "Cognitive Services Contributor"
  principal_id                     = module.api.IDENTITY_PRINCIPAL_ID
  skip_service_principal_aad_check = true
}

# Assign Cognitive Services OpenAI Contributor role to the Web App
resource "azurerm_role_assignment" "openai_contributor" {
  depends_on                       = [module.api]
  scope                            = azurerm_cognitive_account.openai.id
  role_definition_name             = "Cognitive Services OpenAI Contributor"
  principal_id                     = module.api.IDENTITY_PRINCIPAL_ID
  skip_service_principal_aad_check = true
}

resource "azurerm_role_assignment" "multi_cognitive_services_contributor" {
  depends_on                       = [module.api]
  scope                            = data.azurerm_cognitive_account.CognitiveServices.id
  role_definition_name             = "Cognitive Services Contributor"
  principal_id                     = module.api.IDENTITY_PRINCIPAL_ID
  skip_service_principal_aad_check = true
}

# Assign Cognitive Services OpenAI Contributor role to the Web App
resource "azurerm_role_assignment" "speech_contributor" {
  depends_on                       = [module.api]
  scope                            = data.azurerm_cognitive_account.CognitiveServices.id
  role_definition_name             = "Cognitive Services Speech Contributor"
  principal_id                     = module.api.IDENTITY_PRINCIPAL_ID
  skip_service_principal_aad_check = true
}

resource "azurerm_redis_cache_access_policy_assignment" "redis_data_contributor" {
  depends_on         = [module.api]
  name               = "app_service_data_contributor"
  redis_cache_id     = azurerm_redis_cache.redis.id
  access_policy_name = "Data Contributor"
  object_id          = module.api.IDENTITY_PRINCIPAL_ID
  object_id_alias    = "ServicePrincipal"
}
