const http = require('http')
const app = require('../app')

let server
let port

beforeAll(async () => {
  await new Promise(resolve => {
    server = app.listen(0, '127.0.0.1', resolve)
  })
  port = server.address().port
})

afterAll(async () => {
  await new Promise((resolve, reject) => {
    server.close(err => err ? reject(err) : resolve())
  })
})

const request = path => new Promise((resolve, reject) => {
  http.get(`http://127.0.0.1:${port}${path}`, res => {
    let body = ''
    res.on('data', chunk => { body += chunk })
    res.on('end', () => resolve({ status: res.statusCode, body }))
  }).on('error', reject)
})

test('health endpoint reports OK', async () => {
  const res = await request('/health')
  expect(res).toEqual({ status: 200, body: 'ok' })
})

test('version endpoint identifies development builds', async () => {
  const res = await request('/version')
  expect(res).toEqual({ status: 200, body: 'development' })
})
