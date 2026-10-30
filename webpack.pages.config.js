const base = require('./webpack.config')

module.exports = {
  ...base,
  output: {
    ...base.output,
    publicPath: '/full-stack-open-pokedex/'
  }
}
