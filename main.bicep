param location string = 'canadacentral'
param apimResourceGroupName string = 'apim-rg'
param backendResourceGroupName string = 'backend-rg'
param apimName string = 'my-apim-instance'
param appServicePlanName string = 'my-appservice-plan'
param webAppName string = 'my-backend-app'

resource apimRg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: apimResourceGroupName
  location: location
}

resource backendRg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: backendResourceGroupName
  location: location
}

resource apim 'Microsoft.ApiManagement/service@2022-08-01' = {
  name: apimName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: 'admin@contoso.com'
    publisherName: 'Contoso'
  }
  scope: resourceGroup(apimRg.name)
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'F1'
    tier: 'Free'
    capacity: 1
  }
  kind: 'app'
  scope: resourceGroup(backendRg.name)
}

resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppName
  location: location
  kind: 'app'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
  }
  scope: resourceGroup(backendRg.name)
}
