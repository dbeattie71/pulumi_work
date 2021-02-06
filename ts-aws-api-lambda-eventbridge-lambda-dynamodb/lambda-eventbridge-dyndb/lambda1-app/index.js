exports.handler =  async function(event, context) {
  console.log("\n*** EVENT RECEIVED ***: \n" + JSON.stringify(event, null, 2))
  return {
      statusCode: 200,
      body: "Hello, Pulumi!"
  };
}