const path = require('path');

module.exports = {
  plugins: [
    require('postcss-import')(),
    require('postcss-url')({
      url: 'inline',
      basePath: path.resolve(__dirname, 'phorum/static'),
      maxSize: 10 // inline files up to 10 KB
    })
  ]
}
