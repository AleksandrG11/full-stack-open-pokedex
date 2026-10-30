const express = require('express')
const path = require('path')
const app = express()

const PORT = Number(process.env.PORT) || 5000

app.get('/health', (_req, res) => {
  res.status(200).send('ok')
})

app.get('/version', (_req, res) => {
  res.status(200).send(process.env.APP_VERSION || 'development')
})

app.use(express.static('dist'))
app.get('*', (_req, res) => res.sendFile(path.join(__dirname, 'dist', 'index.html')))

if (require.main === module) {
  app.listen(PORT, () => {
    // eslint-disable-next-line no-console
    console.log(`server started on port ${PORT}`)
  })
}

module.exports = app
