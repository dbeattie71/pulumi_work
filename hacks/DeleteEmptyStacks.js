/* 
 * Deletes stacks that are empty (i.e. have no resources) and haven't been touched for "ageDays" days (see code).
 *
 * Parameters
 * orgName - Pulumi organization name
 * accessToken - Pulumi user access token
 * age - (optional) override default age in days to delete
 */


async function DeleteEmptyStacks(orgName, accessToken, age) {

    // Stacks that haven't been updated more than this number of days ago are deleted.
    ageDays = 14

    if (((orgName == null) || (orgName == "")) || ((accessToken == null) || (accessToken == ""))) {
        console.log("***** USAGE ******")
        console.log("***** DeleteEmptyStacks(\"ORGANIZATION_NAME\", \"PULUMI_ACCESS_TOKEN\"")
        console.log(`***** This script will delete stacks that have not been updated in over ${ageDays} ago.`)
        console.log("")
        return
    }

    if (age !=null) {
        ageDays = age
    }

    response = await fetch(`https://api.pulumi.com/api/console/orgs/${orgName}/repos`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'authorization': `token ${accessToken}`
        }
    })

    resp = await response.json()
    repos = resp.repositories

    for (repo of repos) {
        for (project of repo.projects) {
            projectName = project.name
            for (stack of project.stacks) {
                stackName = stack.name
                fullStack = `${orgName}/${projectName}/${stackName}`
                deleteable = false
                if (!stack.hasOwnProperty('lastUpdate')) {
                    deleteable = true
                } else {
                    ageSeconds = ageDays * (60 * 60 * 24)
                    stackLastUpdateTime = stack.lastUpdate.endTime
                    nowTime = Math.round(Date.now()/1000) // bring down to seconds
                    age = nowTime - stackLastUpdateTime
                    console.log("time", `${age}, ${ageSeconds}, ${stackLastUpdateTime}, ${nowTime}`)
                    if ((stack.lastUpdate.resourceCount == 0) && (age > ageSeconds)) {
                        deleteable = true
                    }
                } 
                if (deleteable) {
                    // Delete the stack
                    await deleteStack(fullStack, accessToken)
                } else {
                    console.log("Keeping: ", fullStack)
                }
            }
        }
    }
}

async function deleteStack(fullStack, accessToken) {
    console.log("Deleting: ", fullStack)
    delResp = await fetch(`https://api.pulumi.com/api/stacks/${fullStack}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'authorization': `token ${accessToken}`,
        }
    })
}