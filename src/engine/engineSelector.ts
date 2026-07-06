import type { BaseEngine } from './BaseEngine';
import { BrowserEngine } from './BrowserEngine';
import { LocalEngine } from './LocalEngine';

export type EngineType = 'browser' | 'local';

let currentEngineType: EngineType = 'browser';
let browserEngine: BrowserEngine | null = null;
let localEngine: LocalEngine | null = null;
let localEngineUrl = 'http://localhost:8000';

export function setEngineType(type: EngineType): void {
  currentEngineType = type;
}

export function getEngineType(): EngineType {
  return currentEngineType;
}

export function setLocalEngineUrl(url: string): void {
  localEngineUrl = url;
  if (localEngine) {
    localEngine = new LocalEngine(localEngineUrl);
  }
}

export function getEngine(): BaseEngine {
  if (currentEngineType === 'local') {
    if (!localEngine) {
      localEngine = new LocalEngine(localEngineUrl);
    }
    return localEngine;
  }

  if (!browserEngine) {
    browserEngine = new BrowserEngine();
  }
  return browserEngine;
}
