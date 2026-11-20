// Runs the Next.js CLI the same way in cmd.exe, PowerShell and the Linux image (AD-17): it sets
// NEXT_TELEMETRY_DISABLED=1 and copies the repository's shared text (`../content/*.json`, AD-12) into
// `frontend/content/` (git-ignored) when that folder exists, then starts `next <args>`.
import { spawn } from 'node:child_process';
import { cpSync, existsSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const frontend = join(dirname(fileURLToPath(import.meta.url)), '..');
const shared = join(frontend, '..', 'content');
const copy = join(frontend, 'content');

if (existsSync(shared)) {
  rmSync(copy, { recursive: true, force: true });
  cpSync(shared, copy, { recursive: true });
}

const env = { ...process.env, NEXT_TELEMETRY_DISABLED: '1' };
const nextBin = createRequire(import.meta.url).resolve('next/dist/bin/next');
const child = spawn(process.execPath, [nextBin, ...process.argv.slice(2)], { cwd: frontend, env, stdio: 'inherit' });
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
child.on('exit', (code, signal) => process.exit(signal ? 1 : (code ?? 1)));
