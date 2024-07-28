import { writable } from 'svelte/store';
export const reloadTableSignal = writable(Date.now());