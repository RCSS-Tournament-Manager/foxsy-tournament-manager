// lib/stomp.js
import { writable } from "svelte/store";
import * as StompJs from "@stomp/stompjs";

// Connection state store
export const connectionStateStore = writable("init");
// all states are "init", "connecting", "connected", "failed"

export const credentialsStore = writable(initCredentials());

credentialsStore.subscribe(value => {
    if (typeof localStorage === 'undefined') return;
    if (value.remember) {
        localStorage.setItem("credentials", JSON.stringify(value));
    }
});


function initCredentials() {
    if (typeof localStorage === 'undefined') return {
        username: "admin",
        password: "admin",
        host: "ws://localhost:15676/ws",
        remember: false
    }
    const credentials = localStorage.getItem("credentials");
    if (credentials) {
        try {
            return JSON.parse(credentials);
        } catch (e) {
            return {
                username: "admin",
                password: "admin",
                host: "ws://localhost:15676/ws",
                remember: false
            };
        }
    }
    return {
        username: "admin",
        password: "admin",
        host: "ws://localhost:15676/ws",
        remember: false
    };
}

// Global client object
let client;

// Function to connect to the backend
export function connect(credentials) {
    connectionStateStore.update(_ => "connecting");
    const {
        username,
        password,
        host
    } = credentials;


    try {
        const ws = new WebSocket(host);
        ws.onerror = function (error) {
            console.error("Error while connecting to the backend: ", error);
            connectionStateStore.update(_ => "failed");
        }
        client = StompJs.Stomp.over(ws);


        const on_connect = function () {
            connectionStateStore.update(_ => "connected");
        };
        const on_close = function () {
            connectionStateStore.update(_ => "init");
        };

        const on_error = function (e) {
            connectionStateStore.update(_ => "failed");
            // console.error("Connection error");
            // console.log(e);
            // if (e.isBinaryBody) {
                // console.log(e.body);
            // }
        };

        client.connect(
            username,
            password,
            on_connect,
            on_error,
            on_close,
            "/"
        );
        client.debug = ()=>{};
        
    } catch (error) {
        console.error("Error while connecting to the backend: ", error);
        connectionStateStore.update(_ => "failed");
        return;
    }

}

// Function to subscribe to a queue
export function subscribe(queue, callback, headers = {}) {
    console.log('subscribing to queue', queue)
    if (client && client.connected) {
        // Fetch old messages from the queue
        return client.subscribe(queue, function(d) {
            // console.log('here--', d)
            if (d.body) {
                callback(d);
            }
        },headers);

    } else {
        console.error("Client not connected. Cannot subscribe.");
    }
}

// Function to send a message to a queue
export function sendMessage(queue, message, headers = {}) {

    if (client && client.connected) {
        client.send(queue, headers, message);
    } else {
        console.error("Client not connected. Cannot send message.");
    }
}

// Function to disconnect from the backend
export function disconnect() {
    if (client) {
        client.disconnect(function () {
            connectionStateStore.update(_ => "init");
            console.log("Disconnected");
        });
    }
}