const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

function extractFunction(source, name) {
  const start = source.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `${name} function should exist`);

  const braceStart = source.indexOf('{', start);
  let depth = 0;

  for (let index = braceStart; index < source.length; index++) {
    const char = source[index];
    if (char === '{') depth++;
    if (char === '}') depth--;
    if (depth === 0) return source.slice(start, index + 1);
  }

  throw new Error(`Unable to extract ${name}`);
}

const indexHtml = fs.readFileSync(path.join(__dirname, '..', 'web', 'index.html'), 'utf8');
const generateCSV = eval(`(${extractFunction(indexHtml, 'generateCSV')})`);

assert.equal(
  generateCSV(
    ['Name', 'Email'],
    [
      ['=HYPERLINK("https://example.test","x")', '+SUM(1,1)'],
      ['-cmd', '@SUM(1,1)']
    ]
  ),
  'Name,Email\n"\'=HYPERLINK(""https://example.test"",""x"")","\'+SUM(1,1)"\n\'-cmd,"\'@SUM(1,1)"'
);

assert.equal(
  generateCSV(
    ['Value'],
    [
      [' =cmd'],
      ['\tTabbed'],
      [' safe'],
      ['text']
    ]
  ),
  'Value\n\' =cmd\n\'\tTabbed\n safe\ntext'
);

assert.equal(
  generateCSV(
    ['Header'],
    [
      ['has,comma'],
      ['has "quote"'],
      ['line\nbreak']
    ]
  ),
  'Header\n"has,comma"\n"has ""quote"""\n"line\nbreak"'
);
