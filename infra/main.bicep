targetScope = 'subscription'

@description('Deployment environment suffix, e.g. dev or prod')
param environmentName string = 'dev'

@description('Azure region for all resources')
param location string = 'eastus'

@description('PostgreSQL administrator login')
param postgresAdminLogin string

@secure()
@description('PostgreSQL administrator password')
param postgresAdminPassword string

var resourceGroupName = 'rg-forensic-mvp-${environmentName}'
var tags = {
  project: 'forensic-evidence-fusion'
  environment: environmentName
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module core 'modules/core.bicep' = {
  name: 'core-${environmentName}'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    postgresAdminLogin: postgresAdminLogin
    postgresAdminPassword: postgresAdminPassword
    tags: tags
  }
}

output resourceGroupName string = rg.name
output keyVaultName string = core.outputs.keyVaultName
output storageAccountName string = core.outputs.storageAccountName
output postgresFqdn string = core.outputs.postgresFqdn
output containerAppFqdn string = core.outputs.containerAppFqdn
output staticWebAppHostname string = core.outputs.staticWebAppHostname
