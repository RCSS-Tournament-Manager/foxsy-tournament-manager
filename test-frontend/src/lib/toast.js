import { writable } from 'svelte/store';

export const toasts = writable([]);

export function pushToast({ icon, title, description, type = 'default' }) {
    const id = Math.random().toString(36).substr(2, 9);
    toasts.update(currentToasts => [
        ...currentToasts,
        { id, icon, title, description, type }
    ]);

    // Automatically remove the toast after 3 seconds
    setTimeout(() => {
        toasts.update(currentToasts => currentToasts.filter(toast => toast.id !== id));
    }, 3000);
}