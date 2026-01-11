const express = require('express');
const app = express();
const port = 3001; // Using a different port to avoid conflict

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/sender.html');
});

app.post('/send', (req, res) => {
  console.log('Received data:', req.body);
  res.send('Data received successfully!');
});

app.listen(port, () => {
  console.log(`Sender service listening at http://localhost:${port}`);
});
