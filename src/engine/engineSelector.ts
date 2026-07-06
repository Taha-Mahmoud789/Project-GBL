import type { BaseEngine } from './BaseEngine';
import { BrowserEngine } from './BrowserEngine';
import { LocalEngine } from './LocalEngine';

export type EngineType = 'browser' | 'local' | 'auto';

let currentEngineType: EngineType = 'auto';
let browserEngine: BrowserEngine | null = null;
let localEngine: LocalEngine | null = null;
let localEngineUrl = 'http://localhost:8000';
let serverAvailable: boolean | null = null;

export function setEngineType(type: EngineType): void {
  currentEngineType = type;
}

export function getEngineType(): EngineType {
  return currentEngineType;
}

export function setLocalEngineUrl(url: string): void {
  localEngineUrl = url;
  localEngine = new LocalEngine(localEngineUrl);
  serverAvailable = null; // reset cache
}

export function getLocalEngineUrl(): string {
  return localEngineUrl;
}

/**
 * Check if the FastAPI server is reachable. Caches result for 10 seconds.
 */
export async function checkServerHealth(): Promise<boolean> {
  if (serverAvailable !== null) return serverAvailable;
  const engine = getOrCreateLocalEngine();
  serverAvailable = await engine.healthCheck();
  // Reset cache after 10s
  setTimeout(() => { serverAvailable = null; }, 10_000);
  return serverAvailable;
}

/**
 * Get the current server availability (cached, may be null if not checked yet).
 */
export function isServerAvailable(): boolean | null {
  return serverAvailable;
}

export async function getEngine(): Promise<BaseEngine> {
  if (currentEngineType === 'local') {
    return getOrCreateLocalEngine();
  }

  if (currentEngineType === 'auto') {
    const available = await checkServerHealth();
    if (available) {
      return getOrCreateLocalEngine();
    }
    // Fallback to browser engine (will throw — that's ok for now)
    return getOrCreateBrowserEngine();
  }

  return getOrCreateBrowserEngine();
}

/**
 * Synchronous version — returns local engine if auto-detected as available,
 * otherwise browser engine. Use for non-async contexts.
 */
export function getEngineSync(): BaseEngine {
  if (currentEngineType === 'local') {
    return getOrCreateLocalEngine();
  }

  if (currentEngineType === 'auto' && serverAvailable === true) {
    return getOrCreateLocalEngine();
  }

  return getOrCreateBrowserEngine();
}

function getOrCreateLocalEngine(): LocalEngine {
  if (!localEngine) {
    localEngine = new LocalEngine(localEngineUrl);
  }
  return localEngine;
}

function getOrCreateBrowserEngine(): BrowserEngine {
  if (!browserEngine) {
    browserEngine = new BrowserEngine();
  }
  return browserEngine;
}
