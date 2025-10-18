const fs = require('fs');

try {
  const content = fs.readFileSync('public/rss.xml', 'utf8');
  console.log('First 20 characters (with codes):');
  for(let i = 0; i < Math.min(20, content.length); i++) {
    const char = content[i];
    const code = content.charCodeAt(i);
    console.log(`${i}: '${char}' (${code})`);
  }
  
  console.log('\nFile size:', content.length, 'characters');
  console.log('Starts with XML declaration:', content.startsWith('<?xml'));
  
  // Check for BOM
  if (content.charCodeAt(0) === 0xFEFF) {
    console.log('⚠️  BOM detected at start of file!');
  } else {
    console.log('✅ No BOM detected');
  }
  
  // Check for leading whitespace
  if (content[0] !== '<') {
    console.log('⚠️  File does not start with < character');
  } else {
    console.log('✅ File starts with < character');
  }
  
} catch (error) {
  console.error('Error reading RSS file:', error.message);
}