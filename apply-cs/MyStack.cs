using Pulumi;
using Pulumi.Azure.Core;
using Pulumi.Azure.Storage;

class MyStack : Stack
{
    public MyStack()
    {
        var config = new Pulumi.Config();
        var rgName = config.GetSecret("rgName"); 

        // Create an Azure Resource Group
        var resourceGroupName = rgName.Apply(rgn => {
            var rg = new ResourceGroup(rgn, new ResourceGroupArgs
            {
                Name = rgn,
            });
            return rg.Name;
        });

        var storageAccount = new Account("storage", new AccountArgs
        {
            ResourceGroupName = resourceGroupName,
            AccountReplicationType = "LRS",
            AccountTier = "Standard"
        });

        this.ResourceGroupName = resourceGroupName;
        this.ConnectionString = storageAccount.PrimaryConnectionString;

    }
    [Output] 
    public Output<string> ResourceGroupName { get; set; }
    [Output]
    public Output<string> ConnectionString { get; set; }
}
