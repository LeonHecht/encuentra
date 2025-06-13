// CommonJS: funciona aunque el proyecto sea "type": "module"
module.exports = {
  plugins: [
    require('@tailwindcss/postcss'), // Tailwind 4 postcss shim
    require('autoprefixer'),
  ],
};
