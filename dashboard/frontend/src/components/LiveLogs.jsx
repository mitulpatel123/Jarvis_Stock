import React from 'react';
import { Terminal } from 'lucide-react';

const LiveLogs = ({ logs }) => {
    return (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex items-center gap-2 mb-4">
                <Terminal className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">Live Terminal</h2>
            </div>
            <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1 p-4 bg-black/90 rounded-lg text-green-400 border border-border/50 shadow-inner">
                {logs.map((log, i) => (
                    <div key={i} className="break-words opacity-90 hover:opacity-100 transition-opacity">
                        <span className="opacity-50 mr-2">[{new Date().toLocaleTimeString()}]</span>
                        {typeof log === 'string' ? log : JSON.stringify(log)}
                    </div>
                ))}
                {logs.length === 0 && <div className="text-muted-foreground italic">Waiting for logs...</div>}
            </div>
        </div>
    );
};

export default LiveLogs;
