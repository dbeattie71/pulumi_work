exports.handler = async (event) => {
  console.log('--- processed and event ---')
  console.log(JSON.stringify(event, null, 2))
}