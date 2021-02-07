const AWS = require('aws-sdk')
AWS.config.region = process.env.AWS_REGION || 'us-east-1'
const eventbridge = new AWS.EventBridge()

exports.handler = async (event, context) => {
  // process API Calls ....
  // TBD 

  // Get the info about the infrastructure that was just created/updated by Pulumi
  const { infraInfo } = require('./infra_info.js')
  const eventBusName = infraInfo.eventBusName
  const eventSource = infraInfo.eventSource

  // And now create the event...

  // parameters set up
  const timestamp = Date.now()
  const params = {
    Entries: [ 
    {
      // Event envelope fields
      Source: eventSource,
      EventBusName: eventBusName,
      DetailType: 'transaction',
      Time: timestamp,
      // Main event body
      Detail: JSON.stringify({
        timestamp: timestamp,
        action: 'something-new-happened',
        result: 'it-was-also-good',
      })
    },
  ]}

  // console.log('--- Params ---')
  // console.log(params)
  //const result = JSON.stringify(params) 
  const result = await eventbridge.putEvents(params).promise()

  console.log('--- Response ---')
  console.log(result)  

  return {
      statusCode: 200,
      body: JSON.stringify(params)
  };
}