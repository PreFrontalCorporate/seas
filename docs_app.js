import express from 'express';
import fs from 'fs';
import MarkdownIt from 'markdown-it';

const app = express();
const md = new MarkdownIt();

app.get('/', (req, res) => {
  fs.readFile('./docs/index.md', 'utf8', (err, data) => {
    if (err) {
      res.status(500).send('Could not load docs.');
    } else {
      const htmlContent = md.render(data);
      res.send(`
        <html>
          <head>
            <title>CBB Docs</title>
            <style>
              body { max-width: 800px; margin: auto; padding: 2em; font-family: sans-serif; line-height: 1.6; }
              pre { background: #f4f4f4; padding: 1em; overflow-x: auto; }
              code { background: #f4f4f4; padding: 0.2em 0.4em; }
            </style>
          </head>
          <body>
            ${htmlContent}
          </body>
        </html>
      `);
    }
  });
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`📄 Docs server running on port ${port}`);
});
