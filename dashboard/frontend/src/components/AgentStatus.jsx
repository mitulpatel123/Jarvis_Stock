import React from 'react';
import { Cpu } from 'lucide-react';

const AGENT_LIST = [
    "finnhub_agent", "alpha_vantage_agent", "vision_agent", "technical_agent",
    "sentiment_agent", "execution_agent", "risk_agent", "session_agent",
    "news_agent", "social_agent", "correlation_agent", "volatility_agent"
];

const AgentStatus = ({ agents }) => {
    return (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
                <Cpu className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">System Agents</h2>
            </div>
            <div className="space-y-3">
                {AGENT_LIST.map((agent) => {
                    const isActive = agents[agent] && (Date.now() - agents[agent].last_seen < 60000); // Active if seen in last 60s
                    return (
                        <div key={agent} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 transition-colors">
                            <span className="text-sm font-medium capitalize">{agent.replace('_agent', '').replace('_', ' ')}</span>
                            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500/50'}`} />
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default AgentStatus;
