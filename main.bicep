param location string = 'canadacentral'
param apimResourceGroupName string = 'apim-rg'
param backendResourceGroupName string = 'backend-rg'

resource apimRg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: apimResourceGroupName
  location: location
}

resource backendRg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: backendResourceGroupName
  location: location
}
