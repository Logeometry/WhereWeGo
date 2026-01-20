// Obfuscate built JS bundles in build/static/js/*
const fs = require('fs');
const path = require('path');
const glob = require('glob');
const obfuscator = require('javascript-obfuscator');

const buildJsDir = path.join(__dirname, '..', 'build', 'static', 'js');

function run() {
  if (!fs.existsSync(buildJsDir)) {
    console.error('build/static/js 디렉토리를 찾을 수 없습니다. 먼저 `npm run build`를 실행하세요.');
    process.exit(1);
  }

  const files = glob.sync('**/*.js', {
    cwd: buildJsDir,
    absolute: true,
    nodir: true,
    ignore: '**/*.map',
  });

  if (files.length === 0) {
    console.warn('obfuscate 대상 JS 파일이 없습니다.');
    return;
  }

  files.forEach((filePath) => {
    const original = fs.readFileSync(filePath, 'utf8');
    const result = obfuscator.obfuscate(original, {
      compact: true,
      controlFlowFlattening: true,
      controlFlowFlatteningThreshold: 0.2,
      deadCodeInjection: true,
      deadCodeInjectionThreshold: 0.05,
      disableConsoleOutput: false,
      identifierNamesGenerator: 'hexadecimal',
      renameGlobals: false,
      stringArray: true,
      stringArrayThreshold: 0.75,
      splitStrings: true,
      splitStringsChunkLength: 8,
      transformObjectKeys: true,
      unicodeEscapeSequence: false,
    });

    fs.writeFileSync(filePath, result.getObfuscatedCode(), 'utf8');
    console.log(`Obfuscated: ${path.relative(buildJsDir, filePath)}`);
  });
}

run();
