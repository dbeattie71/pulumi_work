exports.handler =  async function(event, context) {
  console.log("\n*** EVENT RECEIVED ***: \n" + JSON.stringify(event, null, 2))
  const { params } = require('./infra_info.js')
  return {
      statusCode: 200,
      body: `${params.eventBridgeName} --- Hello, Pulumi!`
  };
}